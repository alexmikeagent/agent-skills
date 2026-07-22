from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


EXCLUDED_PARTS = {
    ".git",
    ".local",
    ".screenshots",
    "node_modules",
    "packages",
    "__pycache__",
}


def _git_files(project_root: Path) -> list[Path]:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(project_root),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        return [path for path in project_root.rglob("*") if path.is_file()]
    return [
        project_root / item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    ]


def create_snapshot(project_root: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    manifest = []
    for source in _git_files(project_root):
        if not source.exists() or not source.is_file():
            continue
        relative = source.resolve().relative_to(project_root.resolve())
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest.append(
            {
                "path": relative.as_posix(),
                "sha256": digest,
                "bytes": target.stat().st_size,
            }
        )
    manifest.sort(key=lambda item: item["path"])
    result = {"schema": "uipath-project-snapshot/v1", "files": manifest}
    (destination / ".uipath-snapshot.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result


def remove_snapshot(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
