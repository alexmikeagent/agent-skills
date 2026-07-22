from __future__ import annotations

import json
from typing import Any

from .contracts import normalized_target
from .project_model import WorkflowInfo


def project_map(
    project: dict[str, Any], workflows: dict[str, WorkflowInfo], project_root
) -> dict[str, Any]:
    nodes = []
    edges = []
    for path, workflow in sorted(workflows.items()):
        nodes.append(
            {
                "path": path,
                "arguments": len(workflow.arguments),
                "argument_contracts": [
                    {
                        "name": argument.name,
                        "direction": argument.direction,
                        "type": argument.type_name,
                    }
                    for argument in sorted(
                        workflow.arguments.values(), key=lambda value: value.name
                    )
                ],
                "activities": workflow.activity_count,
                "variables": workflow.variable_count,
                "max_depth": workflow.max_depth,
                "invokes": len(workflow.invokes),
                "invoke_code": workflow.activity_names.count("InvokeCode"),
                "invoke_method": workflow.activity_names.count("InvokeMethod"),
            }
        )
        for invoke in workflow.invokes:
            edges.append(
                {
                    "caller": path,
                    "callee": normalized_target(project_root, workflow, invoke.target),
                    "activity_id": invoke.id_ref,
                }
            )
    return {
        "schema": "uipath-project-map/v1",
        "project": {
            "name": project.get("name", project_root.name),
            "target_framework": project.get("targetFramework"),
            "expression_language": project.get("expressionLanguage"),
            "main": project.get("main"),
        },
        "nodes": nodes,
        "edges": edges,
    }


def mermaid(data: dict[str, Any]) -> str:
    paths = [node["path"] for node in data["nodes"]]
    identifiers = {path: f"W{index}" for index, path in enumerate(paths, start=1)}
    lines = ["flowchart TD"]
    for node in data["nodes"]:
        path = node["path"]
        label = path.replace('"', "'")
        detail = f"{node['activities']} activities · {node['invokes']} invokes"
        lines.append(f'    {identifiers[path]}["{label}<br/>{detail}"]')
    for edge in data["edges"]:
        caller = identifiers.get(edge["caller"])
        callee = identifiers.get(edge["callee"])
        if caller and callee:
            lines.append(f"    {caller} --> {callee}")
    return "\n".join(lines)


def dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=False)
