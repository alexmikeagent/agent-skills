from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .project_model import Finding


def _normalized(value: str) -> str:
    return value.replace("\\", "/").lstrip("./")


def validate_metadata(
    project_root: Path,
    project: dict[str, Any],
    *,
    require_registered_tests: bool = False,
) -> list[Finding]:
    findings: list[Finding] = []
    registrations = project.get("designOptions", {}).get("fileInfoCollection", []) or []
    registered: set[str] = set()
    test_ids: list[str] = []
    for item in registrations:
        file_name = _normalized(str(item.get("fileName", "")))
        test_id = str(item.get("testCaseId", ""))
        if file_name:
            registered.add(file_name)
            if not (project_root / file_name).is_file():
                findings.append(
                    Finding(
                        "META001",
                        "error",
                        f"Registered test file does not exist: {file_name}",
                        "project.json",
                    )
                )
        if test_id:
            test_ids.append(test_id)
    for test_id, count in Counter(test_ids).items():
        if count > 1:
            findings.append(
                Finding(
                    "META002",
                    "error",
                    f"Duplicate testCaseId: {test_id}",
                    "project.json",
                )
            )

    for path in project_root.rglob("TC_*.xaml"):
        relative = path.relative_to(project_root).as_posix()
        if relative not in registered:
            severity = "error" if require_registered_tests else "warning"
            findings.append(
                Finding(
                    "META003",
                    severity,
                    f"Test XAML is not registered: {relative}",
                    relative,
                )
            )

    for entry in project.get("entryPoints", []) or []:
        file_name = _normalized(str(entry.get("filePath", "")))
        if file_name and not (project_root / file_name).is_file():
            findings.append(
                Finding(
                    "META004",
                    "error",
                    f"Entry point does not exist: {file_name}",
                    "project.json",
                )
            )

    entry_points_path = project_root / "entry-points.json"
    if entry_points_path.exists():
        try:
            json.loads(entry_points_path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as error:
            findings.append(
                Finding(
                    "META005",
                    "error",
                    f"entry-points.json is invalid: {error}",
                    "entry-points.json",
                )
            )

    for sidecar in project_root.rglob("*.xaml.json"):
        try:
            json.loads(sidecar.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as error:
            findings.append(
                Finding(
                    "META006",
                    "error",
                    f"XAML sidecar is invalid: {error}",
                    sidecar.relative_to(project_root).as_posix(),
                )
            )
        xaml = Path(str(sidecar)[:-5])
        if not xaml.exists():
            findings.append(
                Finding(
                    "META007",
                    "warning",
                    "XAML sidecar has no matching workflow",
                    sidecar.relative_to(project_root).as_posix(),
                )
            )
    return findings
