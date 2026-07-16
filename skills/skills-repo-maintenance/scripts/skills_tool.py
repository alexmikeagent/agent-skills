#!/usr/bin/env python3
"""Maintain the canonical global skills tree and its generated vault mirror."""

from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


REPO = Path("/Users/aman-mac-work/Documents/PERSONAL/Projects/agent-skills")
SKILLS = REPO / "skills"
RUNTIME = Path("/Users/aman-mac-work/.agents/skills")
LEGACY = Path("/Users/aman-mac-work/.codex/skills")
MIRROR = Path(
    "/Users/aman-mac-work/Documents/PERSONAL/Projects/obsidian-vaults/Second Brain/90 Meta/Skills Mirror"
)
SENTINEL = MIRROR / ".generated-skill-mirror"
LOCK_FILE = REPO / "tooling-lock.json"
MIRRORABLE_SUFFIXES = {".md", ".mdx", ".txt", ".yaml", ".yml", ".json", ".css", ".js", ".mjs", ".py", ".sh"}
SKIP_PARTS = {".git", "node_modules", ".cache", ".tmp", "__pycache__"}


def run(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=check)


def parse_skill(path: Path) -> tuple[str | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None
    if not text.startswith("---\n"):
        return None, None
    end = text.find("\n---", 4)
    if end < 0:
        return None, None
    name = None
    description = None
    for line in text[4:end].splitlines():
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("description:"):
            description = line.split(":", 1)[1].strip().strip("'\"")
    return name, description


def doctor() -> list[str]:
    errors: list[str] = []
    if not SKILLS.is_dir():
        errors.append(f"Canonical skills directory is missing: {SKILLS}")
        return errors
    if not RUNTIME.is_symlink():
        errors.append(f"Runtime path is not a symlink: {RUNTIME}")
    elif RUNTIME.resolve() != SKILLS.resolve():
        errors.append(f"Runtime path resolves to {RUNTIME.resolve()}, expected {SKILLS.resolve()}")
    if LEGACY.exists():
        errors.append(f"Legacy skill tree exists: {LEGACY}")

    names: set[str] = set()
    for directory in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"Missing SKILL.md: {directory}")
            continue
        name, description = parse_skill(skill_file)
        if name != directory.name:
            errors.append(f"Skill name mismatch in {skill_file}: {name!r}")
        if not description:
            errors.append(f"Missing skill description in {skill_file}")
        if name in names:
            errors.append(f"Duplicate skill name: {name}")
        if name:
            names.add(name)

    if LOCK_FILE.is_file():
        lock = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
        for executable in lock.get("executables", {}):
            if shutil.which(executable) is None:
                errors.append(f"Required executable is missing: {executable}")
        for package in lock.get("npm_packages", {}):
            package_file = SKILLS / "mdx-publish" / "node_modules" / package / "package.json"
            if not package_file.is_file():
                errors.append(f"Required MDX package is not installed: {package}")
        forbidden = lock.get("forbidden_terms", [])
        for skill in lock.get("audited_skills", []):
            directory = SKILLS / skill
            if not directory.is_dir():
                errors.append(f"Audited skill is missing: {skill}")
                continue
            for path in directory.rglob("*"):
                if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
                    continue
                if path.suffix.lower() not in MIRRORABLE_SUFFIXES and path.name != "SKILL.md":
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                for term in forbidden:
                    if term.lower() in text.lower():
                        errors.append(f"Forbidden unsupported-tool reference {term!r} in {path}")
    else:
        errors.append(f"Tooling lock is missing: {LOCK_FILE}")
    return errors


def mirrorable(path: Path) -> bool:
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    return path.name.startswith("LICENSE") or path.name == "SKILL.md" or path.suffix.lower() in MIRRORABLE_SUFFIXES


def build_mirror() -> None:
    MIRROR.mkdir(parents=True, exist_ok=True)
    existing = list(MIRROR.iterdir())
    if existing and not SENTINEL.exists():
        raise RuntimeError(f"Refusing to replace non-generated mirror directory: {MIRROR}")
    for child in existing:
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()

    target_skills = MIRROR / "skills"
    target_skills.mkdir(parents=True)
    rows: list[tuple[str, str]] = []
    for directory in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        name, description = parse_skill(directory / "SKILL.md")
        if not name:
            continue
        rows.append((name, description or ""))
        for source in directory.rglob("*"):
            if not source.is_file() or not mirrorable(source):
                continue
            rel = source.relative_to(SKILLS)
            destination = target_skills / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    SENTINEL.write_text("generated; edit only for explicit promotion\n", encoding="utf-8")
    lines = [
        "---",
        "type: skills-catalog",
        "status: generated",
        f"created: {date.today().isoformat()}",
        f"updated: {date.today().isoformat()}",
        "sensitivity: personal",
        "tags:",
        "  - meta/skills",
        "---",
        "",
        "# Global skills mirror",
        "",
        "> [!warning] Generated, not canonical",
        "> The source of truth is `~/.agents/skills`. Run `skills-promote` before preserving an edit made here.",
        "",
        "| Skill | Purpose |",
        "| --- | --- |",
    ]
    for name, description in rows:
        safe_description = description.replace("|", "\\|")
        lines.append(f"| [[skills/{name}/SKILL|{name}]] | {safe_description} |")
    lines.append("")
    (MIRROR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def promote(relative_path: str, apply: bool) -> int:
    source = (MIRROR / relative_path).resolve()
    mirror_root = MIRROR.resolve()
    try:
        rel = source.relative_to(mirror_root)
    except ValueError:
        raise RuntimeError("Promotion path escapes the mirror")
    if not str(rel).startswith("skills/"):
        raise RuntimeError("Only files beneath Skills Mirror/skills can be promoted")
    if not source.is_file():
        raise RuntimeError(f"Mirror file does not exist: {source}")
    destination = SKILLS / rel.relative_to("skills")
    before = destination.read_text(encoding="utf-8") if destination.exists() else ""
    after = source.read_text(encoding="utf-8")
    diff = "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=str(destination),
            tofile=str(source),
        )
    )
    print(diff or "No differences.")
    if not apply or not diff:
        return 0

    original = destination.read_bytes() if destination.exists() else None
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    skill_dir = SKILLS / rel.parts[1]
    validator = SKILLS / "skill-creator" / "scripts" / "quick_validate.py"
    try:
        run([sys.executable, str(validator), str(skill_dir)])
        errors = doctor()
        if errors:
            raise RuntimeError("; ".join(errors))
    except Exception:
        if original is None:
            destination.unlink(missing_ok=True)
        else:
            destination.write_bytes(original)
        raise

    run(["git", "add", str(destination.relative_to(REPO))], cwd=REPO)
    run(["git", "commit", "-m", f"Promote skill mirror change: {rel}"], cwd=REPO)
    remotes = run(["git", "remote"], cwd=REPO).stdout.split()
    if "origin" in remotes:
        run(["git", "push", "origin", "main"], cwd=REPO)
    build_mirror()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("mirror")
    promote_parser = sub.add_parser("promote")
    promote_parser.add_argument("--apply", action="store_true")
    promote_parser.add_argument("path")
    args = parser.parse_args()

    try:
        if args.command == "doctor":
            errors = doctor()
            if errors:
                for error in errors:
                    print(f"[ERROR] {error}")
                return 1
            print(f"[OK] Canonical skills passed: {SKILLS}")
            return 0
        if args.command == "mirror":
            build_mirror()
            print(f"[OK] Skills mirror updated: {MIRROR}")
            return 0
        return promote(args.path, args.apply)
    except (OSError, RuntimeError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

