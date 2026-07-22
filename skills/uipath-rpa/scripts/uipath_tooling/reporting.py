from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .project_model import Finding, gate, now_iso


def validation_result(
    project: dict[str, Any],
    findings: list[Finding],
    scoped_files: list[str],
    started_at: str,
) -> dict[str, Any]:
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    status = "failed" if errors else "passed"
    return {
        "schema": "uipath-validation-result/v1",
        "job_id": None,
        "project": {
            "name": project.get("name"),
            "target_framework": project.get("targetFramework"),
            "expression_language": project.get("expressionLanguage"),
        },
        "environment": {"host_os": "macOS", "runner": "local-static"},
        "scope": {"files": scoped_files},
        "gates": {
            "static": gate(status, f"{errors} error(s), {warnings} warning(s)"),
            "compile": gate("not_run"),
            "execution": gate("not_run"),
            "uat": gate("not_run"),
        },
        "findings": [item.to_dict() for item in findings],
        "tests": [],
        "artifacts": [],
        "started_at": started_at,
        "finished_at": now_iso(),
    }


def text_report(result: dict[str, Any]) -> str:
    project = result.get("project", {})
    lines = [
        f"UiPath validation: {project.get('name') or 'unknown project'}",
        f"L1 static: {result.get('gates', {}).get('static', {}).get('status', 'unknown')}",
        f"L2 compile: {result.get('gates', {}).get('compile', {}).get('status', 'not_run')}",
        f"L3 execution: {result.get('gates', {}).get('execution', {}).get('status', 'not_run')}",
    ]
    findings = result.get("findings", [])
    if findings:
        lines.append("")
        for finding in findings:
            location = finding.get("file", "project")
            if finding.get("line"):
                location += f":{finding['line']}"
            lines.append(
                f"[{finding.get('severity', 'info').upper()}] {finding.get('code')} {location} — {finding.get('message')}"
            )
    else:
        lines.append("No findings.")
    return "\n".join(lines)


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
