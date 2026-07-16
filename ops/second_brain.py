#!/usr/bin/env python3
"""Operate the personal Second Brain and canonical global skills repository."""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


HOME = Path("/Users/aman-mac-work")
MANAGEMENT = HOME / "Documents/PERSONAL/Projects/obsidian-vaults"
VAULT = MANAGEMENT / "Second Brain"
GIT_DIR = MANAGEMENT / ".git-data/second-brain.git"
LOG_DIR = MANAGEMENT / "logs"
LOCK_DIR = MANAGEMENT / ".snapshot.lock"
DRIVE_STAGING = MANAGEMENT / ".drive-staging"
SKILLS_REPO = HOME / "Documents/PERSONAL/Projects/agent-skills"
INSTALLED_RUNTIME = HOME / "Library/Application Support/Second Brain"
SCRIPT_DIR = Path(__file__).resolve().parent
RUNNING_INSTALLED = SCRIPT_DIR.is_relative_to(INSTALLED_RUNTIME)
LAUNCH_AGENT = "com.amanuel.second-brain-snapshot"
CANONICAL_SKILLS_TOOL = (
    SKILLS_REPO / "skills/skills-repo-maintenance/scripts/skills_tool.py"
)
CANONICAL_HEALTH_TOOL = SKILLS_REPO / "skills/vault-health/scripts/vault_health.py"
SKILLS_TOOL = (
    SCRIPT_DIR / "skills_tool.py"
    if RUNNING_INSTALLED and (SCRIPT_DIR / "skills_tool.py").is_file()
    else CANONICAL_SKILLS_TOOL
)
HEALTH_TOOL = (
    SCRIPT_DIR / "vault_health.py"
    if RUNNING_INSTALLED and (SCRIPT_DIR / "vault_health.py").is_file()
    else CANONICAL_HEALTH_TOOL
)
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
    "sb-snapshot": "snapshot",
    "sb-sync": "sync",
    "sb-restore": "restore",
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


def git(*arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    if not GIT_DIR.is_dir():
        raise CommandError(f"Git metadata is missing: {GIT_DIR}")
    return run(
        [
            "git",
            f"--git-dir={GIT_DIR}",
            f"--work-tree={VAULT}",
            *arguments,
        ],
        check=check,
    )


def log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().astimezone().isoformat(timespec="seconds")
    with (LOG_DIR / "second-brain.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp} {message}\n")


@contextlib.contextmanager
def snapshot_lock():
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


def prepare_snapshot() -> None:
    if not VAULT.is_dir():
        raise CommandError(f"Vault is unavailable: {VAULT}")
    refresh_skills_mirror()
    validate_vault()


def git_has_head() -> bool:
    return git("rev-parse", "--verify", "HEAD", check=False).returncode == 0


def commit_changes(prefix: str) -> bool:
    git("add", "-A")
    if git("diff", "--cached", "--quiet", check=False).returncode == 0:
        return False
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    git("commit", "-m", f"{prefix}: {stamp}")
    return True


def remote_exists() -> bool:
    return "origin" in git("remote").stdout.split()


def fetch_origin() -> None:
    if remote_exists():
        git("fetch", "--prune", "origin", "main")


def divergence() -> tuple[int, int]:
    if not remote_exists():
        return 0, 0
    if git("rev-parse", "--verify", "origin/main", check=False).returncode != 0:
        return 0, 0
    values = git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).stdout.split()
    return int(values[0]), int(values[1])


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
    run(
        [RSYNC, "-a", "--delete", f"{DRIVE_STAGING}/", f"{destination}/"],
        capture=True,
    )
    print(f"[OK] Google Drive mirror updated: {destination}")
    return destination


def snapshot() -> int:
    with snapshot_lock():
        prepare_snapshot()
        changed = commit_changes("snapshot")
        if remote_exists():
            fetch_origin()
            ahead, behind = divergence()
            if behind:
                raise CommandError(
                    f"origin/main is {behind} commit(s) ahead; run sb-sync before the next snapshot"
                )
            if ahead:
                git("push", "origin", "main")
        destination = update_drive_mirror()
        outcome = "committed" if changed else "no content changes"
        log(f"snapshot complete ({outcome}); drive={destination or 'skipped'}")
        print(f"[OK] Snapshot complete: {outcome}")
    return 0


def sync() -> int:
    with snapshot_lock():
        prepare_snapshot()
        commit_changes("snapshot before sync")
        if remote_exists():
            fetch_origin()
            _, behind = divergence()
            if behind:
                result = git("rebase", "origin/main", check=False)
                if result.returncode != 0:
                    git("rebase", "--abort", check=False)
                    detail = (result.stderr or result.stdout).strip()
                    raise CommandError(f"Remote changes conflict with the vault: {detail}")
            validate_vault()
            ahead, behind = divergence()
            if behind:
                raise CommandError("Remote changes remain after rebase")
            if ahead:
                git("push", "origin", "main")
        destination = update_drive_mirror()
        log(f"sync complete; drive={destination or 'skipped'}")
        print("[OK] Second Brain is synchronized")
    return 0


def status() -> int:
    print(f"Vault: {VAULT}")
    print(f"Physical: {VAULT.resolve() if VAULT.exists() else 'unavailable'}")
    print(f"Git metadata: {GIT_DIR}")
    print(f"Google Drive mirror: {find_drive_destination() or 'not mounted'}")
    print(f"Canonical skills: {SKILLS_REPO / 'skills'}")
    agents_skills = HOME / ".agents/skills"
    print(
        "Global skills: "
        f"{agents_skills.resolve() if agents_skills.exists() else 'unavailable'}"
    )
    launch_target = f"gui/{os.getuid()}/{LAUNCH_AGENT}"
    launch = run(["launchctl", "print", launch_target], check=False)
    print(
        "Background snapshots: "
        + ("loaded (30-minute interval)" if launch.returncode == 0 else "not loaded")
    )
    if not GIT_DIR.is_dir() or not git_has_head():
        print("Git: not initialized")
        return 1
    print(f"Commit: {git('log', '-1', '--format=%h %cI %s').stdout.strip()}")
    worktree = git("status", "--short").stdout.strip()
    print("Worktree: clean" if not worktree else f"Worktree:\n{worktree}")
    if remote_exists():
        fetch = git("fetch", "--prune", "origin", "main", check=False)
        if fetch.returncode == 0:
            ahead, behind = divergence()
            print(f"Origin: ahead {ahead}, behind {behind}")
        else:
            print(f"Origin: fetch failed ({(fetch.stderr or '').strip()})")
    else:
        print("Origin: not configured")
    return 0


def safe_relative(raw: str) -> str:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or candidate.parts[:1] == (".git",):
        raise CommandError("Restore path must stay inside the vault")
    return str(candidate)


def restore(revision: str, restore_path: str, apply: bool) -> int:
    path_value = safe_relative(restore_path)
    git("rev-parse", "--verify", f"{revision}^{{commit}}")
    summary = git(
        "diff", "--name-status", "HEAD", revision, "--", path_value
    ).stdout.strip()
    print(summary or "No differences for the selected path.")
    if not apply or not summary:
        if not apply:
            print("Dry run only. Re-run with --apply to restore these paths.")
        return 0
    snapshot()
    with snapshot_lock():
        git("restore", f"--source={revision}", "--staged", "--worktree", "--", path_value)
        validate_vault()
        git("commit", "-m", f"restore: {path_value} from {revision}")
        log(f"restored {path_value} from {revision}")
        print(f"[OK] Restored {path_value} from {revision}; run sb-sync to publish")
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
    if command == "restore":
        parser.add_argument("revision")
        parser.add_argument("path", nargs="?", default=".")
        parser.add_argument("--apply", action="store_true")
    else:
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
        if command == "snapshot":
            return snapshot()
        if command == "sync":
            return sync()
        if command == "restore":
            return restore(args.revision, args.path, args.apply)
        return delegate(command, args.arguments)
    except (CommandError, OSError) as exc:
        log(f"ERROR {command}: {exc}")
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
