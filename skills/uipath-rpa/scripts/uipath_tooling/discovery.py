from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class ProjectDiscoveryError(RuntimeError):
    pass


def resolve_project_root(value: str | Path) -> Path:
    candidate = Path(value).expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    for directory in (candidate, *candidate.parents):
        if (directory / "project.json").is_file():
            return directory
    if candidate.is_dir():
        matches = list(candidate.rglob("project.json"))
        if len(matches) == 1:
            return matches[0].parent
        if len(matches) > 1:
            raise ProjectDiscoveryError(
                f"Multiple UiPath projects found below {candidate}; pass the exact project directory"
            )
    raise ProjectDiscoveryError(f"No project.json found from {candidate}")


def load_project_json(project_root: Path) -> dict[str, Any]:
    path = project_root / "project.json"
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProjectDiscoveryError(f"Cannot read {path}: {error}") from error


def all_xaml(project_root: Path) -> list[Path]:
    return sorted(
        path
        for path in project_root.rglob("*.xaml")
        if not any(
            part in {".git", ".local", "node_modules", "packages"}
            for part in path.parts
        )
    )


def _git_lines(project_root: Path, arguments: list[str]) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def scoped_xaml(
    project_root: Path, scope: str, explicit: list[str] | None = None
) -> list[Path]:
    if explicit:
        paths: list[Path] = []
        for value in explicit:
            path = Path(value)
            if not path.is_absolute():
                path = project_root / path
            if path.is_dir():
                paths.extend(sorted(path.rglob("*.xaml")))
            elif path.suffix.lower() == ".xaml":
                paths.append(path)
        return sorted({path.resolve() for path in paths if path.exists()})
    if scope == "all":
        return all_xaml(project_root)

    diff_args = ["diff", "--name-only", "--diff-filter=ACMR"]
    if scope == "staged":
        diff_args.append("--cached")
    diff_args.extend(["--", "*.xaml"])
    names = _git_lines(project_root, diff_args)
    if scope == "changed":
        names.extend(
            _git_lines(
                project_root,
                ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "--", "*.xaml"],
            )
        )
        names.extend(
            _git_lines(
                project_root,
                ["ls-files", "--others", "--exclude-standard", "--", "*.xaml"],
            )
        )
    result = []
    for name in dict.fromkeys(names):
        path = (project_root / name).resolve()
        if path.exists() and path.suffix.lower() == ".xaml":
            result.append(path)
    return sorted(result)


def relative(project_root: Path, path: Path) -> str:
    return path.resolve().relative_to(project_root.resolve()).as_posix()
