from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .project_model import Finding, WorkflowInfo


FLUENT_AFTER_NEWLINE = re.compile(
    r"\.\s*\r?\n\s*(?:Select|Where|Distinct|OrderBy|OrderByDescending|Take|ToList|ToArray)\s*\(",
    re.IGNORECASE,
)
UNQUALIFIED_REGEX = re.compile(r"(?<![\w.])Regex\.")


def expressions(root: ET.Element):
    for element in root.iter():
        for value in element.attrib.values():
            if value.startswith("[") and value.endswith("]"):
                yield value[1:-1]
        if element.text:
            value = element.text.strip()
            if value.startswith("[") and value.endswith("]"):
                yield value[1:-1]


def parenthesis_error(expression: str) -> str | None:
    depth = 0
    in_string = False
    index = 0
    while index < len(expression):
        character = expression[index]
        if character == '"':
            if (
                in_string
                and index + 1 < len(expression)
                and expression[index + 1] == '"'
            ):
                index += 2
                continue
            in_string = not in_string
        elif not in_string and character == "(":
            depth += 1
        elif not in_string and character == ")":
            depth -= 1
            if depth < 0:
                return "closes a parenthesis before opening it"
        index += 1
    if in_string:
        return "contains an unterminated VB string literal"
    if depth:
        return f"has {depth} unclosed parenthesis(es)"
    return None


def check_workflow(workflow: WorkflowInfo) -> list[Finding]:
    imports_regex = (
        "<x:String>System.Text.RegularExpressions</x:String>" in workflow.source
    )
    findings: list[Finding] = []
    for number, expression in enumerate(expressions(workflow.root), start=1):
        error = parenthesis_error(expression)
        if error:
            findings.append(
                Finding(
                    "VB001",
                    "error",
                    f"Expression {number} {error}",
                    workflow.relative_path,
                )
            )
        if FLUENT_AFTER_NEWLINE.search(expression):
            findings.append(
                Finding(
                    "VB002",
                    "error",
                    f"Expression {number} continues a fluent member after a physical newline",
                    workflow.relative_path,
                    remediation="Keep the chain on one line or split it into typed Assign activities.",
                )
            )
        if UNQUALIFIED_REGEX.search(expression) and not imports_regex:
            findings.append(
                Finding(
                    "VB003",
                    "error",
                    f"Expression {number} uses unqualified Regex without the VB namespace import",
                    workflow.relative_path,
                    remediation="Import System.Text.RegularExpressions or fully qualify Regex.",
                )
            )
    return findings


def check_path(path: Path) -> list[str]:
    try:
        workflow = parse_for_compatibility(path)
    except ET.ParseError as error:
        return [f"XML parse failed: {error}"]
    return [finding.message for finding in check_workflow(workflow)]


def parse_for_compatibility(path: Path) -> WorkflowInfo:
    from .xaml_parser import parse_workflow

    return parse_workflow(path, path.parent)
