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
    "logs",
    "node_modules",
    "output",
    "outputs",
    "packages",
    "runs",
    "__pycache__",
}
SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    "credentials.json",
    "secrets.json",
}
SENSITIVE_SUFFIXES = {".key", ".kdbx", ".p12", ".pem", ".pfx"}
MAX_SNAPSHOT_FILE_BYTES = 50 * 1024 * 1024
SAFE_UNTRACKED_SUFFIXES = {
    ".config",
    ".cs",
    ".json",
    ".nuspec",
    ".props",
    ".targets",
    ".vb",
    ".xaml",
    ".xml",
}


class SnapshotSafetyError(ValueError):
    pass


def _git_file_list(project_root: Path, *arguments: str) -> tuple[int, list[Path]]:
    completed = subprocess.run(
        ["git", "-C", str(project_root), "ls-files", *arguments, "-z"],
        check=False,
        capture_output=True,
    )
    return completed.returncode, [
        project_root / item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    ]


def _project_files(project_root: Path) -> list[tuple[Path, bool | None]]:
    """Return each project file and whether Git tracks it."""

    tracked_code, tracked = _git_file_list(project_root, "--cached")
    if tracked_code != 0:
        return [
            (path, None) for path in project_root.rglob("*") if path.is_file()
        ]
    _, untracked = _git_file_list(project_root, "--others", "--exclude-standard")
    return [(path, True) for path in tracked] + [
        (path, False) for path in untracked
    ]


def _relative_source(
    project_root: Path, source: Path, *, tracked: bool | None
) -> Path | None:
    if not source.exists() or not source.is_file():
        return None
    if source.is_symlink():
        raise SnapshotSafetyError(f"Snapshot refuses symlink: {source}")
    try:
        relative = source.resolve().relative_to(project_root.resolve())
    except ValueError as error:
        raise SnapshotSafetyError(
            f"Snapshot source escapes the project root: {source}"
        ) from error
    lowered_parts = {part.lower() for part in relative.parts}
    if lowered_parts.intersection(EXCLUDED_PARTS):
        if tracked is True:
            raise SnapshotSafetyError(
                f"Snapshot refuses to omit tracked file in an excluded path: "
                f"{relative.as_posix()}"
            )
        return None
    lowered_name = relative.name.lower()
    if lowered_name in SENSITIVE_NAMES or relative.suffix.lower() in SENSITIVE_SUFFIXES:
        raise SnapshotSafetyError(
            f"Snapshot refuses credential-like file: {relative.as_posix()}"
        )
    if tracked is False and relative.suffix.lower() not in SAFE_UNTRACKED_SUFFIXES:
        raise SnapshotSafetyError(
            f"Snapshot refuses untracked non-source file: {relative.as_posix()}"
        )
    if source.stat().st_size > MAX_SNAPSHOT_FILE_BYTES:
        raise SnapshotSafetyError(
            f"Snapshot refuses file larger than {MAX_SNAPSHOT_FILE_BYTES} bytes: "
            f"{relative.as_posix()}"
        )
    return relative


def create_snapshot(project_root: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    manifest = []
    try:
        for source, tracked in _project_files(project_root):
            relative = _relative_source(project_root, source, tracked=tracked)
            if relative is None:
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
                    "tracked": tracked,
                }
            )
        manifest.sort(key=lambda item: item["path"])
        result = {"schema": "uipath-project-snapshot/v1", "files": manifest}
        (destination / ".uipath-snapshot.json").write_text(
            json.dumps(result, indent=2) + "\n", encoding="utf-8"
        )
        return result
    except Exception:
        remove_snapshot(destination)
        raise


def remove_snapshot(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
