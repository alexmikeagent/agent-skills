from __future__ import annotations

import re
from pathlib import Path

from .project_model import Finding, WorkflowInfo


TYPE_ALIASES = {
    "x:string": "system.string",
    "s:string": "system.string",
    "system.string": "system.string",
    "x:boolean": "system.boolean",
    "s:boolean": "system.boolean",
    "system.boolean": "system.boolean",
    "x:int32": "system.int32",
    "s:int32": "system.int32",
    "system.int32": "system.int32",
    "x:int64": "system.int64",
    "s:int64": "system.int64",
    "system.int64": "system.int64",
    "x:double": "system.double",
    "s:double": "system.double",
    "system.double": "system.double",
    "x:decimal": "system.decimal",
    "s:decimal": "system.decimal",
    "system.decimal": "system.decimal",
    "x:datetime": "system.datetime",
    "s:datetime": "system.datetime",
    "system.datetime": "system.datetime",
    "x:object": "system.object",
    "s:object": "system.object",
    "system.object": "system.object",
    "sd:datatable": "system.data.datatable",
    "system.data.datatable": "system.data.datatable",
}


def normalize_type(value: str) -> str:
    compact = re.sub(r"\s+", "", value).lower()
    for alias in sorted(TYPE_ALIASES, key=len, reverse=True):
        compact = compact.replace(alias, TYPE_ALIASES[alias])
    return compact


def normalized_target(project_root: Path, caller: WorkflowInfo, target: str) -> str:
    target = target.replace("\\", "/")
    direct = project_root / target
    if direct.exists():
        return direct.resolve().relative_to(project_root.resolve()).as_posix()
    relative = caller.path.parent / target
    if relative.exists():
        return relative.resolve().relative_to(project_root.resolve()).as_posix()
    return target


def validate_contracts(
    project_root: Path,
    workflows: dict[str, WorkflowInfo],
    scoped: set[str],
) -> list[Finding]:
    findings: list[Finding] = []
    for caller_path, caller in workflows.items():
        if caller_path not in scoped:
            continue
        for invoke in caller.invokes:
            target = normalized_target(project_root, caller, invoke.target)
            callee = workflows.get(target)
            if callee is None:
                findings.append(
                    Finding(
                        "INV001",
                        "error",
                        f"Invoked workflow does not exist: {invoke.target}",
                        caller_path,
                        activity_id=invoke.id_ref,
                        evidence=invoke.display_name,
                    )
                )
                continue
            for binding in invoke.arguments:
                expected = callee.arguments.get(binding.name)
                if expected is None:
                    findings.append(
                        Finding(
                            "INV002",
                            "error",
                            f"Unknown argument {binding.name} for {target}",
                            caller_path,
                            activity_id=invoke.id_ref,
                        )
                    )
                    continue
                if binding.direction != expected.direction:
                    findings.append(
                        Finding(
                            "INV003",
                            "error",
                            f"Argument {binding.name} direction is {binding.direction}; callee expects {expected.direction}",
                            caller_path,
                            activity_id=invoke.id_ref,
                            evidence=f"target={target}",
                        )
                    )
                if normalize_type(binding.type_name) != normalize_type(
                    expected.type_name
                ):
                    findings.append(
                        Finding(
                            "INV004",
                            "error",
                            f"Argument {binding.name} type is {binding.type_name}; callee expects {expected.type_name}",
                            caller_path,
                            activity_id=invoke.id_ref,
                            evidence=f"normalized={normalize_type(binding.type_name)} vs {normalize_type(expected.type_name)}",
                        )
                    )
    return findings
