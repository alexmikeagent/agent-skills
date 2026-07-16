#!/usr/bin/env python3
"""Build and install the dedicated Second Brain snapshot runtime."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


HOME = Path("/Users/aman-mac-work")
REPO = HOME / "Documents/PERSONAL/Projects/agent-skills"
RUNTIME = HOME / "Library/Application Support/Second Brain"
APP = RUNTIME / "Second Brain Snapshot.app"
CONTENTS = APP / "Contents"
MACOS = CONTENTS / "MacOS"
RESOURCES = CONTENTS / "Resources"
LAUNCH_AGENTS = HOME / "Library/LaunchAgents"
LOGS = HOME / "Library/Logs/Second Brain"
LABEL = "com.amanuel.second-brain-snapshot"
DOMAIN = f"gui/{os.getuid()}"
PLIST_NAME = f"{LABEL}.plist"


def run(*command: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "command failed").strip()
        raise SystemExit(f"{' '.join(command)}: {detail}")
    return result


def require(binary: str) -> str:
    resolved = shutil.which(binary)
    if not resolved:
        raise SystemExit(f"Required installed tool is missing: {binary}")
    return resolved


def install() -> None:
    python = require("python3")
    swiftc = require("swiftc")
    codesign = require("codesign")
    plutil = require("plutil")

    RUNTIME.mkdir(parents=True, exist_ok=True)
    MACOS.mkdir(parents=True, exist_ok=True)
    RESOURCES.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)

    copies = {
        REPO / "ops/second_brain.py": RESOURCES / "second_brain.py",
        REPO / "skills/skills-repo-maintenance/scripts/skills_tool.py": RESOURCES
        / "skills_tool.py",
        REPO / "skills/vault-health/scripts/vault_health.py": RESOURCES
        / "vault_health.py",
        REPO / "launchd/SecondBrainSnapshot-Info.plist": CONTENTS / "Info.plist",
        REPO / f"launchd/{PLIST_NAME}": LAUNCH_AGENTS / PLIST_NAME,
    }
    for source, destination in copies.items():
        if not source.is_file():
            raise SystemExit(f"Required source is missing: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    for obsolete in ("second_brain.py", "skills_tool.py", "vault_health.py"):
        (RUNTIME / obsolete).unlink(missing_ok=True)
    shutil.rmtree(RUNTIME / "__pycache__", ignore_errors=True)

    executable = MACOS / "Second Brain Snapshot"
    run(
        swiftc,
        str(REPO / "launchd/SecondBrainSnapshot.swift"),
        "-o",
        str(executable),
    )
    executable.chmod(0o755)
    python_sources = [str(path) for path in copies.values() if path.suffix == ".py"]
    run(
        python,
        "-c",
        (
            "import pathlib, sys\n"
            "for name in sys.argv[1:]:\n"
            "    source = pathlib.Path(name).read_text(encoding='utf-8')\n"
            "    compile(source, name, 'exec')\n"
        ),
        *python_sources,
    )
    run(
        codesign,
        "--force",
        "--sign",
        "-",
        "--identifier",
        "com.amanuel.second-brain-snapshot-app",
        str(APP),
    )
    run(plutil, "-lint", str(CONTENTS / "Info.plist"))
    run(plutil, "-lint", str(LAUNCH_AGENTS / PLIST_NAME))
    print(f"[OK] Installed snapshot app: {APP}")
    print(f"[OK] Installed LaunchAgent: {LAUNCH_AGENTS / PLIST_NAME}")


def load() -> None:
    executable = APP / "Contents/MacOS/Second Brain Snapshot"
    plist = LAUNCH_AGENTS / PLIST_NAME
    if not executable.is_file() or not plist.is_file():
        raise SystemExit("Snapshot runtime is not installed; run without --load first")
    run(require("codesign"), "--verify", "--deep", "--strict", str(APP))
    run(require("plutil"), "-lint", str(plist))
    target = f"{DOMAIN}/{LABEL}"
    run("launchctl", "bootout", DOMAIN, str(plist), check=False)
    run("launchctl", "bootstrap", DOMAIN, str(plist))
    run("launchctl", "enable", target)
    run("launchctl", "kickstart", "-k", target)
    print(f"[OK] Loaded and started {target}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--load",
        action="store_true",
        help="load the already-installed LaunchAgent after the app has Full Disk Access",
    )
    args = parser.parse_args()
    if args.load:
        load()
    else:
        install()


if __name__ == "__main__":
    main()
