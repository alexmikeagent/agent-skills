from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any

from .project_model import Finding, WorkflowInfo
from .xaml_parser import attribute, local_name


class PolicyError(RuntimeError):
    pass


def load_policy(skill_root: Path, value: str | None) -> dict[str, Any]:
    name = value or "baseline"
    path = Path(name)
    if not path.exists():
        if not path.suffix:
            path = skill_root / "assets" / "policies" / f"{name}.json"
        else:
            path = skill_root / "assets" / "policies" / name
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PolicyError(f"Cannot load policy {name}: {error}") from error
    allowed = {
        "schema",
        "name",
        "forbid_activities",
        "leaf_forbid_invoke_workflow",
        "require_boundary_logs",
        "log_after_activities",
        "require_expanded_assign",
        "max_activity_count",
        "max_depth",
        "phi_sensitive_tokens",
        "phi_safe_markers",
        "sensitive_tokens",
        "exclude_path_patterns",
    }
    unknown = sorted(set(policy) - allowed)
    if unknown:
        raise PolicyError(f"Unknown policy key(s): {', '.join(unknown)}")
    return policy


def _excluded(path: str, policy: dict[str, Any]) -> bool:
    return any(
        fnmatch.fnmatch(path, pattern)
        for pattern in policy.get("exclude_path_patterns", [])
    )


def validate_policy(workflow: WorkflowInfo, policy: dict[str, Any]) -> list[Finding]:
    if _excluded(workflow.relative_path, policy):
        return []
    findings: list[Finding] = []
    forbidden = set(policy.get("forbid_activities", []))
    for name in sorted(forbidden.intersection(workflow.activity_names)):
        findings.append(
            Finding(
                "POL001",
                "error",
                f"Forbidden activity is present: {name}",
                workflow.relative_path,
            )
        )
    if policy.get("leaf_forbid_invoke_workflow") and workflow.invokes:
        findings.append(
            Finding(
                "POL002",
                "error",
                "Leaf workflow invokes another workflow",
                workflow.relative_path,
            )
        )

    if policy.get("require_boundary_logs"):
        lowered = workflow.source.lower()
        if "start:" not in lowered and "log message - start" not in lowered:
            findings.append(
                Finding(
                    "POL003",
                    "error",
                    "Workflow has no start boundary log",
                    workflow.relative_path,
                )
            )
        if "end:" not in lowered and "log message - end" not in lowered:
            findings.append(
                Finding(
                    "POL004",
                    "error",
                    "Workflow has no end boundary log",
                    workflow.relative_path,
                )
            )

    log_after = set(policy.get("log_after_activities", []))
    if log_after:
        for parent in workflow.root.iter():
            children = [
                child for child in list(parent) if "." not in local_name(child.tag)
            ]
            for index, child in enumerate(children):
                name = local_name(child.tag)
                if name not in log_after:
                    continue
                following = (
                    local_name(children[index + 1].tag)
                    if index + 1 < len(children)
                    else ""
                )
                if following != "LogMessage":
                    findings.append(
                        Finding(
                            "POL005",
                            "warning",
                            f"{name} is not followed by a storytelling Log Message in the same container",
                            workflow.relative_path,
                            activity_id=attribute(child, "WorkflowViewState.IdRef"),
                        )
                    )

    if policy.get("require_expanded_assign"):
        for element in workflow.root.iter():
            if local_name(element.tag) != "Assign":
                continue
            child_names = {local_name(child.tag) for child in list(element)}
            if not {"Assign.To", "Assign.Value"}.issubset(child_names):
                findings.append(
                    Finding(
                        "POL006",
                        "warning",
                        "Assign is not serialized in expanded Studio-readable form",
                        workflow.relative_path,
                        activity_id=attribute(element, "WorkflowViewState.IdRef"),
                    )
                )

    max_activities = policy.get("max_activity_count")
    if isinstance(max_activities, int) and workflow.activity_count > max_activities:
        findings.append(
            Finding(
                "POL007",
                "warning",
                f"Workflow has {workflow.activity_count} activities; policy maximum is {max_activities}",
                workflow.relative_path,
            )
        )
    max_depth = policy.get("max_depth")
    if isinstance(max_depth, int) and workflow.max_depth > max_depth:
        findings.append(
            Finding(
                "POL008",
                "warning",
                f"Workflow XML depth is {workflow.max_depth}; policy maximum is {max_depth}",
                workflow.relative_path,
            )
        )

    sensitive = [
        token.lower()
        for token in policy.get(
            "sensitive_tokens", policy.get("phi_sensitive_tokens", [])
        )
    ]
    safe_markers = [marker.lower() for marker in policy.get("phi_safe_markers", [])]
    for element in workflow.root.iter():
        if local_name(element.tag) != "LogMessage":
            continue
        message = (attribute(element, "Message") or "").lower()
        if any(marker in message for marker in safe_markers):
            continue
        matched = next((token for token in sensitive if token in message), None)
        if matched:
            findings.append(
                Finding(
                    "POL009",
                    "warning",
                    f"Log message may include sensitive transaction data: {matched}",
                    workflow.relative_path,
                    activity_id=attribute(element, "WorkflowViewState.IdRef"),
                )
            )
    return findings
