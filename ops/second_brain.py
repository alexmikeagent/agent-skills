#!/usr/bin/env python3
"""Operate the personal Second Brain and canonical global skills repository."""

from __future__ import annotations

import argparse
import contextlib
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


HOME = Path("/Users/aman-mac-work")
MANAGEMENT = HOME / "Documents/PERSONAL/Projects/obsidian-vaults"
VAULT = MANAGEMENT / "Second Brain"
LOG_DIR = MANAGEMENT / "logs"
LOCK_DIR = MANAGEMENT / ".refresh.lock"
DRIVE_STAGING = MANAGEMENT / ".drive-staging"
SKILLS_REPO = HOME / "Documents/PERSONAL/Projects/agent-skills"
SKILLS_TOOL = (
    SKILLS_REPO / "skills/skills-repo-maintenance/scripts/skills_tool.py"
)
HEALTH_TOOL = SKILLS_REPO / "skills/vault-health/scripts/vault_health.py"
PYTHON = shutil.which("python3") or "/usr/bin/python3"
RSYNC = "/usr/bin/rsync"
MIRROR_EXTENSIONS = {
    ".base",
    ".canvas",
    ".gif",
    ".html",
    ".jpeg",
    ".jpg",
    ".json",
    ".md",
    ".mdx",
    ".pdf",
    ".png",
    ".txt",
    ".webp",
}
MIRROR_SKIP_PARTS = {
    ".git",
    ".obsidian",
    ".trash",
    "logs",
    "node_modules",
}
COMMANDS = {
    "sb-status": "status",
    "sb-refresh": "refresh",
    "skills-doctor": "skills-doctor",
    "skills-mirror": "skills-mirror",
    "skills-promote": "skills-promote",
    "vault-health": "vault-health",
}


class CommandError(RuntimeError):
    pass


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "command failed").strip()
        raise CommandError(f"{' '.join(command)}: {detail}")
    return result


def log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with (LOG_DIR / "second-brain.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {message}\n")


@contextlib.contextmanager
def refresh_lock():
    try:
        LOCK_DIR.mkdir()
    except FileExistsError as exc:
        raise CommandError(
            f"Another Second Brain operation is active: {LOCK_DIR}"
        ) from exc
    try:
        yield
    finally:
        with contextlib.suppress(OSError):
            LOCK_DIR.rmdir()


def call_python(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    result = run([PYTHON, str(script), *arguments], cwd=script.parent)
    if result.stdout:
        print(result.stdout.rstrip())
    return result


def refresh_skills_mirror() -> None:
    call_python(SKILLS_TOOL, "mirror")


def validate_vault() -> None:
    call_python(HEALTH_TOOL, "--vault", str(VAULT))


def prepare_refresh() -> None:
    if not VAULT.is_dir():
        raise CommandError(f"Vault is unavailable: {VAULT}")
    refresh_skills_mirror()
    validate_vault()


def find_drive_destination() -> Path | None:
    cloud = HOME / "Library/CloudStorage"
    candidates = sorted(cloud.glob("GoogleDrive-*/My Drive"))
    for candidate in candidates:
        if candidate.is_dir():
            return candidate / "Obsidian/Second Brain (Read Only)"
    return None


def mirrorable(source: Path) -> bool:
    try:
        relative = source.relative_to(VAULT)
    except ValueError:
        return False
    if any(part in MIRROR_SKIP_PARTS for part in relative.parts):
        return False
    return source.is_file() and source.suffix.lower() in MIRROR_EXTENSIONS


def stage_drive_mirror() -> None:
    if DRIVE_STAGING.exists():
        shutil.rmtree(DRIVE_STAGING)
    DRIVE_STAGING.mkdir(parents=True)
    for source in VAULT.rglob("*"):
        if not mirrorable(source):
            continue
        destination = DRIVE_STAGING / source.relative_to(VAULT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    (DRIVE_STAGING / ".generated-read-only-mirror").write_text(
        "Generated from the validated Second Brain vault. Edit the live vault, not this copy.\n",
        encoding="utf-8",
    )


def update_drive_mirror(required: bool = False) -> Path | None:
    destination = find_drive_destination()
    if destination is None:
        message = "Google Drive Desktop is not mounted; Drive mirror skipped"
        if required:
            raise CommandError(message)
        print(f"[WARN] {message}")
        log(message)
        return None
    sentinel = destination / ".generated-read-only-mirror"
    if destination.exists() and any(destination.iterdir()) and not sentinel.exists():
        raise CommandError(
            f"Refusing to replace a non-generated Drive directory: {destination}"
        )
    stage_drive_mirror()
    destination.mkdir(parents=True, exist_ok=True)
    command = [
        RSYNC,
        "-a",
        "--whole-file",
        "--delete",
        f"{DRIVE_STAGING}/",
        f"{destination}/",
    ]
    last_detail = "unknown error"
    for attempt in range(1, 4):
        result = run(command, check=False, capture=True)
        if result.returncode == 0:
            break
        last_detail = (result.stderr or result.stdout or "").strip() or (
            f"exit code {result.returncode}"
        )
        if attempt < 3:
            message = (
                f"Drive mirror attempt {attempt} failed ({last_detail}); retrying"
            )
            print(f"[WARN] {message}")
            log(message)
            time.sleep(attempt * 2)
    else:
        raise CommandError(
            f"{' '.join(command)} failed after 3 attempts: {last_detail}"
        )
    print(f"[OK] Google Drive mirror updated: {destination}")
    return destination


def refresh() -> int:
    with refresh_lock():
        prepare_refresh()
        destination = update_drive_mirror()
        log(f"refresh complete; drive={destination or 'skipped'}")
        print("[OK] Second Brain refresh complete")
    return 0


def status() -> int:
    print(f"Vault: {VAULT}")
    print(f"Physical: {VAULT.resolve() if VAULT.exists() else 'unavailable'}")
    print("Source control: disabled")
    print(f"Google Drive mirror: {find_drive_destination() or 'not mounted'}")
    print(f"Canonical skills: {SKILLS_REPO / 'skills'}")
    agents_skills = HOME / ".agents/skills"
    print(
        "Global skills: "
        f"{agents_skills.resolve() if agents_skills.exists() else 'unavailable'}"
    )
    print("Background refresh: disabled")
    return 0


def delegate(command: str, arguments: list[str]) -> int:
    if command == "vault-health":
        result = run([PYTHON, str(HEALTH_TOOL), *arguments], check=False)
    else:
        subcommand = command.removeprefix("skills-")
        result = run(
            [PYTHON, str(SKILLS_TOOL), subcommand, *arguments],
            cwd=SKILLS_TOOL.parent,
            check=False,
        )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode


def parser_for(command: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=command)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    return parser


def main() -> int:
    invoked = Path(sys.argv[0]).name
    if invoked in COMMANDS:
        command = COMMANDS[invoked]
        argv = sys.argv[1:]
    else:
        root = argparse.ArgumentParser(prog=invoked)
        root.add_argument("command", choices=sorted(set(COMMANDS.values())))
        known, argv = root.parse_known_args()
        command = known.command
    args = parser_for(command).parse_args(argv)
    try:
        if command == "status":
            return status()
        if command == "refresh":
            return refresh()
        return delegate(command, args.arguments)
    except (CommandError, OSError) as exc:
        log(f"ERROR {command}: {exc}")
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
