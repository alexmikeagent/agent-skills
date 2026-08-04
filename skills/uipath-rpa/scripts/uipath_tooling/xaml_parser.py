from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from .project_model import (
    Finding,
    InvokeArgument,
    InvokeInfo,
    WorkflowArgument,
    WorkflowInfo,
)


NON_ACTIVITY_NAMES = {
    "Activity",
    "ActivityAction",
    "ActivityFunc",
    "Argument",
    "Boolean",
    "Collection",
    "Dictionary",
    "Double",
    "InArgument",
    "InOutArgument",
    "Int32",
    "Members",
    "Null",
    "OutArgument",
    "Property",
    "String",
    "Variable",
}

STABLE_ACTIVITY_NAMES = {
    "Activity",
    "AddDataColumn",
    "AddDataRow",
    "Assign",
    "Break",
    "BuildDataTable",
    "Continue",
    "Delay",
    "DoWhile",
    "ElseIf",
    "ForEach",
    "GetRowItem",
    "If",
    "InvokeWorkflowFile",
    "LogMessage",
    "MultipleAssign",
    "Parallel",
    "Pick",
    "Rethrow",
    "Sequence",
    "Switch",
    "Throw",
    "TryCatch",
    "While",
}


def local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1]


def attribute(element: ET.Element, name: str) -> str | None:
    for key, value in element.attrib.items():
        if local_name(key) == name:
            return value
    return None


def direction_and_type(type_value: str) -> tuple[str, str]:
    match = re.match(
        r"\s*(InOutArgument|InArgument|OutArgument)\s*\((.*)\)\s*$", type_value
    )
    if not match:
        return "Unknown", type_value.strip()
    direction = {"InArgument": "In", "OutArgument": "Out", "InOutArgument": "InOut"}[
        match.group(1)
    ]
    return direction, match.group(2).strip()


def _depth(element: ET.Element, level: int = 1) -> int:
    children = list(element)
    if not children:
        return level
    return max(_depth(child, level + 1) for child in children)


def parse_workflow(path: Path, project_root: Path) -> WorkflowInfo:
    source = path.read_text(encoding="utf-8-sig")
    root = ET.fromstring(source)
    arguments: dict[str, WorkflowArgument] = {}
    invokes: list[InvokeInfo] = []
    id_refs: list[str] = []
    activity_names: list[str] = []
    variable_count = 0

    for element in root.iter():
        name = local_name(element.tag)
        if name == "Property":
            argument_name = attribute(element, "Name")
            type_value = attribute(element, "Type")
            if argument_name and type_value:
                direction, type_name = direction_and_type(type_value)
                arguments[argument_name] = WorkflowArgument(
                    argument_name, direction, type_name
                )
        if name == "Variable":
            variable_count += 1
        for key, value in element.attrib.items():
            if local_name(key) == "WorkflowViewState.IdRef":
                id_refs.append(value)
        if name == "WorkflowViewState.IdRef" and element.text and element.text.strip():
            id_refs.append(element.text.strip())
        if (
            "." not in name
            and name not in NON_ACTIVITY_NAMES
            and not name.endswith("Reference")
        ):
            activity_names.append(name)
        if name == "InvokeWorkflowFile":
            target = attribute(element, "WorkflowFileName") or ""
            invoke_arguments: list[InvokeArgument] = []
            argument_container = next(
                (
                    child
                    for child in list(element)
                    if local_name(child.tag) == "InvokeWorkflowFile.Arguments"
                ),
                None,
            )
            if argument_container is not None:
                for child in list(argument_container):
                    child_name = local_name(child.tag)
                    if child_name not in {"InArgument", "OutArgument", "InOutArgument"}:
                        continue
                    key = attribute(child, "Key")
                    type_name = attribute(child, "TypeArguments") or ""
                    if key:
                        invoke_arguments.append(
                            InvokeArgument(
                                key,
                                {
                                    "InArgument": "In",
                                    "OutArgument": "Out",
                                    "InOutArgument": "InOut",
                                }[child_name],
                                type_name,
                            )
                        )
            invokes.append(
                InvokeInfo(
                    target=target,
                    display_name=attribute(element, "DisplayName")
                    or "Invoke Workflow File",
                    id_ref=attribute(element, "WorkflowViewState.IdRef"),
                    arguments=invoke_arguments,
                )
            )

    relative_path = path.resolve().relative_to(project_root.resolve()).as_posix()
    return WorkflowInfo(
        path=path,
        relative_path=relative_path,
        root=root,
        source=source,
        arguments=arguments,
        invokes=invokes,
        id_refs=id_refs,
        activity_names=activity_names,
        activity_count=len(activity_names),
        variable_count=variable_count,
        max_depth=_depth(root),
    )


def duplicate_id_refs(workflow: WorkflowInfo) -> list[str]:
    counts = Counter(workflow.id_refs)
    return sorted(value for value, count in counts.items() if count > 1)


def naming_findings(
    workflow: WorkflowInfo, maximum_length: int = 30
) -> list[Finding]:
    """Report UiPath's default argument and variable name length findings."""
    findings: list[Finding] = []
    rules = {
        "Property": ("ST-NMG-016", "argument"),
        "Variable": ("ST-NMG-008", "variable"),
    }
    for element in workflow.root.iter():
        element_name = local_name(element.tag)
        if element_name not in rules:
            continue
        identifier = attribute(element, "Name") or ""
        if len(identifier) <= maximum_length:
            continue
        code, kind = rules[element_name]
        findings.append(
            Finding(
                code,
                "warning",
                f"{kind.capitalize()} name exceeds {maximum_length} characters: "
                f"{identifier} ({len(identifier)})",
                workflow.relative_path,
                remediation=(
                    f"Shorten the {kind} name to {maximum_length} characters or fewer "
                    "and update every expression, invoke binding, and entry-point sidecar."
                ),
            )
        )
    return findings


def serialization_findings(
    project_root: Path,
    workflow: WorkflowInfo,
    workflows: dict[str, WorkflowInfo],
) -> list[Finding]:
    previous_names: set[str] = set()
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), "show", f"HEAD:{workflow.relative_path}"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0:
            previous_root = ET.fromstring(completed.stdout)
            previous_names = {
                local_name(element.tag)
                for element in previous_root.iter()
                if "." not in local_name(element.tag)
                and local_name(element.tag) not in NON_ACTIVITY_NAMES
            }
    except (OSError, ET.ParseError):
        pass
    sibling_names = {
        name
        for path, other in workflows.items()
        if path != workflow.relative_path
        for name in other.activity_names
    }
    novel = (
        set(workflow.activity_names)
        - previous_names
        - sibling_names
        - STABLE_ACTIVITY_NAMES
    )
    return [
        Finding(
            "ACT001",
            "warning",
            f"Activity serialization is new to the project scope: {name}",
            workflow.relative_path,
            remediation="Confirm the tag and properties against installed package documentation or pass the L2 Windows build.",
        )
        for name in sorted(novel)
    ]
