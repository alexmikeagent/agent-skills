#!/usr/bin/env python3
"""Read-only heuristic linter for the design-uipath-workflows house standard."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence


TOOL_VERSION = "1.0.0"
SCHEMA = "design-uipath-workflows/audit-v1"

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}

ANNOTATION_HEADINGS = (
    "Purpose",
    "Runs in",
    "Inputs",
    "Outputs",
    "Side effects",
    "Assumptions",
    "Expectations",
    "Static values",
    "Failure behavior",
    "Sensitive data",
)

NON_ACTIVITY_NAMES = {
    "Activity",
    "ActivityAction",
    "ActivityFunc",
    "Argument",
    "Array",
    "AssignOperation",
    "Boolean",
    "Catch",
    "Collection",
    "DelegateInArgument",
    "DelegateOutArgument",
    "Dictionary",
    "Double",
    "Finally",
    "InArgument",
    "InOutArgument",
    "Int32",
    "Int64",
    "KeyValuePair",
    "List",
    "Literal",
    "Members",
    "Null",
    "Object",
    "OutArgument",
    "Property",
    "RuntimeArgument",
    "State",
    "String",
    "Transition",
    "Variable",
    "VisualBasicReference",
    "VisualBasicValue",
}

# Keep the house size benchmark calibrated to the existing COE parser and the
# 53-count reference workflow. This intentionally counts serialized Catch and
# delegate nodes; naming/log checks use the narrower visible-activity predicate.
SIZE_NON_ACTIVITY_NAMES = {
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

ROOT_TYPES = {"Sequence", "Flowchart", "StateMachine"}
PASSIVE_CONTAINERS = {"Sequence", "Flowchart", "TryCatch"}
DECISIONS = {"If", "Switch", "FlowDecision"}
LOOPS = {"ForEach", "ForEachRow", "While", "DoWhile"}
TERMINATORS = {"Throw", "Rethrow", "Break", "Continue", "TerminateWorkflow"}

CANONICAL_ACTIVITY_NAMES = {
    "AddDataColumn": "Add Data Column",
    "AddDataRow": "Add Data Row",
    "CheckAppState": "Check App State",
    "DoWhile": "Do While",
    "ForEach": "For Each",
    "ForEachRow": "For Each Row",
    "InvokeCode": "Invoke Code",
    "InvokeMethod": "Invoke Method",
    "InvokeWorkflowFile": "Invoke Workflow File",
    "LogMessage": "Log Message",
    "MultipleAssign": "Multiple Assign",
    "NClick": "Click",
    "NTypeInto": "Type Into",
    "SendControlKey": "Send Control Key",
    "StateMachine": "State Machine",
    "TakeScreenshot": "Take Screenshot",
    "TerminalSendControlKey": "Send Control Key",
    "TerminalSession": "Terminal Session",
    "TerminalSetFieldAtPosition": "Set Field at Position",
    "TerminalWaitScreenText": "Wait Screen Text",
    "TerminateWorkflow": "Terminate Workflow",
    "TryCatch": "Try Catch",
    "TypeInto": "Type Into",
    "UseApplicationBrowser": "Use Application/Browser",
    "WriteLine": "Write Line",
}

DEFAULT_PROTECTED_PATHS = (
    "Main.xaml",
    "Framework/InitAllSettings.xaml",
    "Framework/InitAllApplications.xaml",
    "Framework/GetTransactionData.xaml",
    "Framework/Process.xaml",
    "Framework/SetTransactionStatus.xaml",
    "Framework/RetryCurrentTransaction.xaml",
    "Framework/CloseAllApplications.xaml",
    "Framework/KillAllProcesses.xaml",
    "Framework/TakeScreenshot.xaml",
)

GENERATED_DIRECTORIES = {
    ".git",
    ".local",
    ".objects",
    ".project",
    "bin",
    "obj",
    "output",
    "packages",
}

SOFT_ABBREVIATIONS = {
    "Account": "Acct",
    "Application": "App",
    "Configuration": "Config",
    "Document": "Doc",
    "Eligibility": "Elig",
    "Estimate": "Est",
    "Information": "Info",
    "Initialization": "Init",
    "Insurance": "Ins",
    "Management": "Mgmt",
    "Number": "Num",
    "Processing": "Proc",
    "Request": "Req",
    "Response": "Resp",
    "Secondary": "Sec",
    "Terminal": "Term",
    "Transaction": "Txn",
    "Verification": "Veri",
}

HARD_ABBREVIATIONS = {
    "Account": "ACCT",
    "Application": "APP",
    "Configuration": "CFG",
    "Patient": "PAT",
    "Terminal": "TER",
    "Transaction": "TXN",
    "Verification": "VERI",
}

FILLER_WORDS = {"A", "An", "And", "For", "From", "Of", "The", "To", "With"}

KNOWN_VERBS = {
    "Add",
    "Build",
    "Calculate",
    "Check",
    "Close",
    "Create",
    "Delete",
    "Download",
    "Enter",
    "Extract",
    "Get",
    "Initialize",
    "Load",
    "Login",
    "Logout",
    "Move",
    "Open",
    "Parse",
    "Process",
    "Read",
    "Save",
    "Search",
    "Send",
    "Set",
    "Submit",
    "Update",
    "Upload",
    "Validate",
    "Verify",
    "Wait",
    "Write",
}

SENSITIVE_NAME_PARTS = (
    "account",
    "address",
    "birth",
    "claim",
    "credential",
    "dob",
    "email",
    "exception",
    "healthplan",
    "invoice",
    "member",
    "medical",
    "message",
    "mrn",
    "name",
    "password",
    "patient",
    "path",
    "payload",
    "phone",
    "screen",
    "selector",
    "ssn",
    "url",
    "username",
)

DEFAULT_SAFE_NAME = re.compile(
    r"^(?:int|bn|dec)(?:Attempt|Can|Count|Delay|Duration|Elapsed|Has|Index|"
    r"Is|Iteration|Limit|Max|Min|Progress|Retry|Should|Simulation|Timeout|Total)",
    re.IGNORECASE,
)

NON_WAIVABLE_RULES = {
    "UIPATH-WF-002",
    "UIPATH-UI-001",
}


class ConfigurationError(ValueError):
    """Raised when CLI or project configuration cannot be trusted."""


@dataclass(frozen=True)
class Waiver:
    rule: str
    workflow: str
    rationale: str
    approver: str
    expiration: date

    @property
    def active(self) -> bool:
        return self.expiration >= date.today()


@dataclass
class StyleConfig:
    application_aliases: tuple[str, ...] = ()
    abbreviations: dict[str, str] = field(default_factory=dict)
    safe_values: tuple[str, ...] = ()
    sensitive_values: tuple[str, ...] = ()
    loop_threshold: int = 10
    loop_progress_interval: int = 100
    protected_paths: tuple[str, ...] = DEFAULT_PROTECTED_PATHS
    waivers: tuple[Waiver, ...] = ()


@dataclass
class Finding:
    rule: str
    severity: str
    source: str
    path: str
    message: str
    suggestion: str | None = None
    waived: bool = False
    original_severity: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {key: value for key, value in asdict(self).items() if value is not None}


@dataclass
class AuditResult:
    project: Path
    scope: str
    files: list[str]
    findings: list[Finding]
    operational_errors: list[str] = field(default_factory=list)

    def sorted_findings(self) -> list[Finding]:
        return sorted(
            self.findings,
            key=lambda item: (
                SEVERITY_ORDER[item.severity],
                item.path.casefold(),
                item.rule,
                item.message,
            ),
        )

    def counts(self) -> dict[str, int]:
        counts = Counter(item.severity for item in self.findings)
        return {name: counts.get(name, 0) for name in ("error", "warning", "info")}


def local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1]


def attribute(element: ET.Element, name: str) -> str | None:
    for key, value in element.attrib.items():
        if local_name(key) == name:
            return value
    return None


def element_text(element: ET.Element) -> str:
    return " ".join(part.strip() for part in element.itertext() if part.strip())


def is_activity(element: ET.Element) -> bool:
    name = local_name(element.tag)
    return (
        "." not in name
        and name not in NON_ACTIVITY_NAMES
        and not name.endswith("Reference")
    )


def is_size_activity(element: ET.Element) -> bool:
    name = local_name(element.tag)
    return (
        "." not in name
        and name not in SIZE_NON_ACTIVITY_NAMES
        and not name.endswith("Reference")
    )


def canonical_activity_name(name: str) -> str:
    if name in CANONICAL_ACTIVITY_NAMES:
        return CANONICAL_ACTIVITY_NAMES[name]
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", name)


def expression_for_log(element: ET.Element) -> str:
    message = attribute(element, "Message")
    if message is not None:
        return message.strip()
    for descendant in element.iter():
        if local_name(descendant.tag) in {"InArgument", "VisualBasicValue"}:
            text = element_text(descendant)
            if text:
                return text
    return element_text(element)


def log_level(element: ET.Element) -> str:
    level = attribute(element, "Level") or attribute(element, "LogLevel")
    if level:
        return level.rsplit(".", 1)[-1].strip("[] ")
    return "Info"


def split_camel(value: str) -> list[str]:
    return re.findall(r"[A-Z]+(?=[A-Z][a-z]|[0-9]|$)|[A-Z]?[a-z]+|[0-9]+", value)


def join_name(application: str | None, prefix: str | None, tokens: Sequence[str]) -> str:
    body = "".join(tokens)
    if application is not None:
        return f"{application}_{body}"
    return f"{prefix or ''}{body}"


def shorten_workflow_stem(
    stem: str,
    abbreviations: dict[str, str] | None = None,
    maximum_filename_length: int = 40,
) -> tuple[str, list[tuple[str, str]]]:
    """Return the shortest readable suggestion needed to fit the filename limit."""

    application: str | None = None
    prefix: str | None = None
    action = stem
    if "_" in stem:
        application, action = stem.split("_", 1)
    else:
        prefix = next((item for item in ("Init", "Pro", "End", "Util") if stem.startswith(item)), None)
        if prefix:
            action = stem[len(prefix) :]

    tokens = split_camel(action)
    changes: list[tuple[str, str]] = []
    filtered: list[str] = []
    for token in tokens:
        if token in FILLER_WORDS:
            changes.append((token, ""))
        else:
            filtered.append(token)
    tokens = filtered

    def current_length() -> int:
        return len(join_name(application, prefix, tokens)) + len(".xaml")

    if current_length() <= maximum_filename_length:
        return join_name(application, prefix, tokens), changes

    custom = abbreviations or {}
    stages = (SOFT_ABBREVIATIONS, custom, HARD_ABBREVIATIONS)
    for replacements in stages:
        candidates = sorted(
            (
                (len(token) - len(replacements[token]), index, token, replacements[token])
                for index, token in enumerate(tokens)
                if token in replacements and len(replacements[token]) < len(token)
            ),
            reverse=True,
        )
        for _saving, index, original, replacement in candidates:
            if current_length() <= maximum_filename_length:
                break
            if tokens[index] != original:
                continue
            tokens[index] = replacement
            changes.append((original, replacement))
        if current_length() <= maximum_filename_length:
            break

    if current_length() > maximum_filename_length:
        candidates = sorted(
            ((len(token), index, token) for index, token in enumerate(tokens[1:], start=1) if len(token) > 4),
            reverse=True,
        )
        for _length, index, original in candidates:
            if current_length() <= maximum_filename_length:
                break
            replacement = original[:3].upper()
            tokens[index] = replacement
            changes.append((original, replacement))

    return join_name(application, prefix, tokens), changes


def _expect_type(value: object, expected: type, field_name: str) -> object:
    if not isinstance(value, expected):
        raise ConfigurationError(f"{field_name} must be {expected.__name__}.")
    return value


def load_config(project: Path, explicit_path: Path | None = None) -> StyleConfig:
    config_path = explicit_path or project / ".uipath-style.json"
    if not config_path.exists():
        return StyleConfig()
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Cannot read {config_path}: {exc}") from exc
    _expect_type(raw, dict, "configuration")
    allowed = {
        "application_aliases",
        "abbreviations",
        "safe_value_classifications",
        "loop_threshold",
        "loop_progress_interval",
        "protected_paths",
        "waivers",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ConfigurationError(f"Unknown configuration field(s): {', '.join(unknown)}")

    aliases = raw.get("application_aliases", [])
    abbreviations = raw.get("abbreviations", {})
    classifications = raw.get("safe_value_classifications", {})
    protected = raw.get("protected_paths", [])
    waiver_rows = raw.get("waivers", [])
    for value, expected, name in (
        (aliases, list, "application_aliases"),
        (abbreviations, dict, "abbreviations"),
        (classifications, dict, "safe_value_classifications"),
        (protected, list, "protected_paths"),
        (waiver_rows, list, "waivers"),
    ):
        _expect_type(value, expected, name)
    if any(not isinstance(item, str) for item in aliases + protected):
        raise ConfigurationError("application_aliases and protected_paths must contain strings.")
    if any(not isinstance(key, str) or not isinstance(value, str) for key, value in abbreviations.items()):
        raise ConfigurationError("abbreviations must map strings to shorter strings.")
    if any(not value or len(value) >= len(key) for key, value in abbreviations.items()):
        raise ConfigurationError("Every abbreviation must be non-empty and shorter than its source word.")
    unknown_classes = set(classifications) - {"safe", "sensitive"}
    if unknown_classes:
        raise ConfigurationError("safe_value_classifications accepts only safe and sensitive.")
    safe = classifications.get("safe", [])
    sensitive = classifications.get("sensitive", [])
    if not isinstance(safe, list) or not isinstance(sensitive, list):
        raise ConfigurationError("safe and sensitive classifications must be lists.")
    if any(not isinstance(item, str) for item in safe + sensitive):
        raise ConfigurationError("safe and sensitive classifications must contain strings.")

    loop_threshold = raw.get("loop_threshold", 10)
    progress_interval = raw.get("loop_progress_interval", 100)
    if not isinstance(loop_threshold, int) or loop_threshold < 1:
        raise ConfigurationError("loop_threshold must be a positive integer.")
    if not isinstance(progress_interval, int) or progress_interval < 1:
        raise ConfigurationError("loop_progress_interval must be a positive integer.")

    waivers: list[Waiver] = []
    required = {"rule", "workflow", "rationale", "approver", "expiration"}
    for index, row in enumerate(waiver_rows):
        if not isinstance(row, dict) or set(row) != required:
            raise ConfigurationError(
                f"waivers[{index}] must contain exactly: {', '.join(sorted(required))}."
            )
        if any(not isinstance(row[key], str) or not row[key].strip() for key in required):
            raise ConfigurationError(f"waivers[{index}] fields must be non-empty strings.")
        try:
            expiration = date.fromisoformat(row["expiration"])
        except ValueError as exc:
            raise ConfigurationError(f"waivers[{index}].expiration must be YYYY-MM-DD.") from exc
        waivers.append(
            Waiver(
                rule=row["rule"],
                workflow=row["workflow"],
                rationale=row["rationale"],
                approver=row["approver"],
                expiration=expiration,
            )
        )

    return StyleConfig(
        application_aliases=tuple(aliases),
        abbreviations=dict(abbreviations),
        safe_values=tuple(safe),
        sensitive_values=tuple(sensitive),
        loop_threshold=loop_threshold,
        loop_progress_interval=progress_interval,
        protected_paths=DEFAULT_PROTECTED_PATHS + tuple(protected),
        waivers=tuple(waivers),
    )


def is_generated(path: Path, project: Path) -> bool:
    relative = path.resolve().relative_to(project.resolve())
    return any(part in GENERATED_DIRECTORIES for part in relative.parts)


def relative_path(path: Path, project: Path) -> str:
    try:
        return path.resolve().relative_to(project.resolve()).as_posix()
    except ValueError as exc:
        raise ConfigurationError(f"Selected path is outside the project: {path}") from exc


def is_protected(relative: str, config: StyleConfig) -> bool:
    if Path(relative).name.startswith("TC_"):
        return True
    return any(fnmatch.fnmatchcase(relative, pattern) for pattern in config.protected_paths)


def all_xaml_files(project: Path) -> list[Path]:
    return sorted(
        path
        for path in project.rglob("*.xaml")
        if path.is_file() and not is_generated(path, project)
    )


def changed_xaml_files(project: Path) -> list[Path]:
    root_result = subprocess.run(
        ["git", "-C", str(project), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if root_result.returncode != 0:
        detail = root_result.stderr.strip() or root_result.stdout.strip() or "Not a Git checkout."
        raise ConfigurationError(f"Cannot resolve changed XAML files: {detail}")
    git_root = Path(root_result.stdout.strip()).resolve()
    commands = (
        ["git", "-C", str(git_root), "diff", "--name-only", "--diff-filter=ACMR", "HEAD", "--", "*.xaml"],
        ["git", "-C", str(git_root), "ls-files", "--others", "--exclude-standard", "--", "*.xaml"],
    )
    names: set[str] = set()
    for command in commands:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "Git command failed."
            raise ConfigurationError(f"Cannot resolve changed XAML files: {detail}")
        names.update(line.strip() for line in completed.stdout.splitlines() if line.strip())
    files: list[Path] = []
    for name in names:
        path = (git_root / name).resolve()
        try:
            path.relative_to(project.resolve())
        except ValueError:
            continue
        if path.is_file():
            files.append(path)
    return sorted(files)


def resolve_scope(project: Path, scope: str, selected: Sequence[str]) -> list[Path]:
    if scope == "all":
        return all_xaml_files(project)
    if scope == "changed":
        return changed_xaml_files(project)
    if not selected:
        raise ConfigurationError("--scope selected requires at least one path after --files.")
    files: list[Path] = []
    for value in selected:
        candidate = Path(value)
        path = candidate if candidate.is_absolute() else project / candidate
        relative_path(path, project)
        if not path.is_file():
            raise ConfigurationError(f"Selected XAML does not exist: {path}")
        if path.suffix.casefold() != ".xaml":
            raise ConfigurationError(f"Selected path is not XAML: {path}")
        files.append(path)
    return sorted(set(files))


def _parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _depth_map(root: ET.Element) -> dict[ET.Element, int]:
    depths = {root: 0}
    stack = [root]
    while stack:
        parent = stack.pop()
        for child in parent:
            depths[child] = depths[parent] + 1
            stack.append(child)
    return depths


def find_root_visual(root: ET.Element) -> ET.Element | None:
    depths = _depth_map(root)
    candidates = [element for element in root.iter() if local_name(element.tag) in ROOT_TYPES]
    return min(candidates, key=lambda item: depths[item]) if candidates else None


def root_annotation(element: ET.Element) -> str:
    for key, value in element.attrib.items():
        if local_name(key).endswith("AnnotationText"):
            return value.strip()
    for child in element:
        if local_name(child.tag).endswith("AnnotationText"):
            return element_text(child)
    return ""


def immediate_activities(element: ET.Element) -> list[ET.Element]:
    found: list[ET.Element] = []

    def visit(node: ET.Element) -> None:
        if is_activity(node):
            found.append(node)
            return
        for child in node:
            visit(child)

    for child in element:
        visit(child)
    return found


def first_executable(element: ET.Element) -> ET.Element | None:
    if is_activity(element):
        name = local_name(element.tag)
        if name in PASSIVE_CONTAINERS:
            children = immediate_activities(element)
            return first_executable(children[0]) if children else None
        return element
    for child in element:
        result = first_executable(child)
        if result is not None:
            return result
    return None


def _target_from_container(element: ET.Element) -> str | None:
    for descendant in element.iter():
        if local_name(descendant.tag) != "OutArgument":
            continue
        match = re.search(r"\[\s*([A-Za-z_]\w*)\s*\]", element_text(descendant))
        if match:
            return match.group(1)
    value = attribute(element, "To")
    if value:
        match = re.search(r"\[?\s*([A-Za-z_]\w*)\s*\]?", value)
        return match.group(1) if match else None
    return None


def _value_from_container(element: ET.Element) -> str | None:
    value = attribute(element, "Value")
    if value:
        return value.strip()
    for descendant in element.iter():
        if local_name(descendant.tag) in {"InArgument", "VisualBasicValue", "Literal"}:
            text = element_text(descendant)
            if text:
                return text.strip()
    return None


def assignment_pairs(element: ET.Element) -> list[tuple[str, str | None]]:
    name = local_name(element.tag)
    containers = [element]
    if name == "MultipleAssign":
        containers = [item for item in element.iter() if local_name(item.tag) == "AssignOperation"]
    pairs: list[tuple[str, str | None]] = []
    for container in containers:
        target_container = next(
            (
                child
                for child in container
                if local_name(child.tag).split(".")[-1] == "To"
            ),
            container,
        )
        value_container = next(
            (
                child
                for child in container
                if local_name(child.tag).split(".")[-1] == "Value"
            ),
            container,
        )
        target = _target_from_container(target_container)
        if target:
            pairs.append((target, _value_from_container(value_container)))
    return pairs


def assignment_targets(element: ET.Element) -> list[str]:
    return [target for target, _value in assignment_pairs(element)]


def literal_assignment(value: str | None) -> str | None:
    if not value:
        return None
    expression = value.strip()
    if expression.startswith("[") and expression.endswith("]"):
        expression = expression[1:-1].strip()
    if re.fullmatch(r"True|False|-?\d+(?:\.\d+)?", expression, re.I):
        return expression
    string_match = re.fullmatch(r'"([^"\r\n]*)"', expression)
    if string_match and string_match.group(1):
        return string_match.group(1)
    return None


def strip_string_literals(expression: str) -> str:
    return re.sub(r'"(?:[^"]|"")*"', "", expression)


def contains_identifier(expression: str, name: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])", expression) is not None


def value_classification(name: str, config: StyleConfig) -> str:
    if any(fnmatch.fnmatchcase(name, pattern) for pattern in config.sensitive_values):
        return "sensitive"
    if any(fnmatch.fnmatchcase(name, pattern) for pattern in config.safe_values):
        return "safe"
    if any(part in name.casefold() for part in SENSITIVE_NAME_PARTS):
        return "sensitive"
    if DEFAULT_SAFE_NAME.search(name):
        return "safe"
    return "sensitive"


def expected_type_prefix(type_name: str) -> str | None:
    lowered = type_name.casefold()
    ordered = (
        ("datatable", "dt_"),
        ("datarow", "dr"),
        ("dictionary", "dict"),
        ("list", "lst"),
        ("terminalconnection", "tc"),
        ("exception", "ex"),
        ("boolean", "bn"),
        ("string", "str"),
        ("int32", "int"),
        ("int64", "int"),
        ("integer", "int"),
        ("decimal", "dec"),
        ("double", "dec"),
    )
    return next((prefix for marker, prefix in ordered if marker in lowered), None)


def direction_and_type(type_value: str) -> tuple[str | None, str]:
    match = re.match(r"\s*(InOutArgument|InArgument|OutArgument)\s*\((.*)\)\s*$", type_value)
    if not match:
        return None, type_value.strip()
    direction = {"InArgument": "in_", "OutArgument": "out_", "InOutArgument": "io_"}[match.group(1)]
    return direction, match.group(2).strip()


def add(
    findings: list[Finding],
    rule: str,
    severity: str,
    source: str,
    path: str,
    message: str,
    suggestion: str | None = None,
) -> None:
    findings.append(Finding(rule, severity, source, path, message, suggestion))


def _audit_filename(
    path: Path,
    relative: str,
    config: StyleConfig,
    collisions: dict[str, list[str]],
    findings: list[Finding],
) -> None:
    filename = path.name
    stem = path.stem
    if len(filename) > 40:
        suggestion, changes = shorten_workflow_stem(stem, config.abbreviations)
        detail = ", ".join(f"{old}→{new or 'removed'}" for old, new in changes)
        candidate = f"{suggestion}.xaml"
        if len(candidate) <= 40 and candidate.casefold() not in collisions:
            remediation = f"Rename to {candidate}"
            if detail:
                remediation += f" ({detail})."
        else:
            remediation = "Shorten the verb-object pointer and recheck case-insensitive collisions."
        add(
            findings,
            "HOUSE-NAME-001",
            "error",
            "House",
            relative,
            f"Complete filename is {len(filename)} characters; the limit is 40.",
            remediation,
        )

    if "_" in stem:
        pieces = stem.split("_")
        valid = len(pieces) == 2 and all(re.fullmatch(r"[A-Z][A-Za-z0-9]*", piece or "") for piece in pieces)
        if not valid:
            add(
                findings,
                "HOUSE-NAME-002",
                "error",
                "House",
                relative,
                "Application workflow names must use [Application]_[Verb][Object] with one underscore.",
            )
        else:
            application, action = pieces
            if config.application_aliases and application not in config.application_aliases:
                add(
                    findings,
                    "HOUSE-NAME-004",
                    "warning",
                    "House",
                    relative,
                    f"Application alias {application!r} is not in project configuration.",
                )
            first_word = split_camel(action)[0] if split_camel(action) else ""
            if first_word and first_word not in KNOWN_VERBS:
                add(
                    findings,
                    "HOUSE-NAME-005",
                    "warning",
                    "House",
                    relative,
                    f"Application action {action!r} does not begin with a recognized verb.",
                    "Use a compact verb-object pointer or document the domain-specific verb.",
                )
    elif not re.fullmatch(r"(?:Init|Pro|End|Util)[A-Z][A-Za-z0-9]*", stem):
        add(
            findings,
            "HOUSE-NAME-002",
            "error",
            "House",
            relative,
            "Non-application workflow names must begin with Init, Pro, End, or Util and use UpperCamelCase without an underscore.",
        )

    matches = collisions.get(filename.casefold(), [])
    if len(matches) > 1:
        add(
            findings,
            "HOUSE-NAME-003",
            "error",
            "House",
            relative,
            f"Filename collides case-insensitively with: {', '.join(item for item in matches if item != relative)}.",
        )


def _audit_annotation(
    root_visual: ET.Element,
    relative: str,
    findings: list[Finding],
) -> None:
    annotation = root_annotation(root_visual)
    if not annotation:
        add(
            findings,
            "HOUSE-ANN-001",
            "error",
            "House",
            relative,
            "Root workflow annotation is missing.",
            "Add all ten required headings and use None for an empty section.",
        )
        return
    positions: list[int] = []
    missing: list[str] = []
    matches: dict[str, re.Match[str]] = {}
    for heading in ANNOTATION_HEADINGS:
        match = re.search(rf"(?im)^\s*{re.escape(heading)}\s*:\s*", annotation)
        if match is None:
            missing.append(heading)
        else:
            positions.append(match.start())
            matches[heading] = match
    if missing:
        add(
            findings,
            "HOUSE-ANN-001",
            "error",
            "House",
            relative,
            f"Annotation is missing heading(s): {', '.join(missing)}.",
        )
        return
    if positions != sorted(positions):
        add(
            findings,
            "HOUSE-ANN-002",
            "warning",
            "House",
            relative,
            "Annotation headings are not in the required order.",
        )
    ordered = sorted(matches.items(), key=lambda item: item[1].start())
    empty = []
    for index, (heading, match) in enumerate(ordered):
        end = ordered[index + 1][1].start() if index + 1 < len(ordered) else len(annotation)
        if not annotation[match.end() : end].strip():
            empty.append(heading)
    if empty:
        add(
            findings,
            "HOUSE-ANN-003",
            "error",
            "House",
            relative,
            f"Annotation section(s) are blank: {', '.join(empty)}. Use None explicitly.",
        )


def _audit_activity_names(
    activities: Sequence[ET.Element],
    root_visual: ET.Element,
    relative: str,
    findings: list[Finding],
) -> None:
    names: list[str] = []
    for element in activities:
        if element is root_visual:
            continue
        activity_type = local_name(element.tag)
        display = attribute(element, "DisplayName")
        if not display:
            add(
                findings,
                "HOUSE-ACT-001",
                "error",
                "House",
                relative,
                f"{canonical_activity_name(activity_type)} has no DisplayName.",
            )
            continue
        names.append(display)
        if " - " not in display:
            add(
                findings,
                "HOUSE-ACT-001",
                "error",
                "House",
                relative,
                f"Activity DisplayName {display!r} must use [Activity name] - [specific action].",
            )
            continue
        prefix, description = display.split(" - ", 1)
        canonical = canonical_activity_name(activity_type)
        if prefix.casefold() != canonical.casefold():
            add(
                findings,
                "HOUSE-ACT-003",
                "warning",
                "House",
                relative,
                f"DisplayName {display!r} does not retain canonical activity name {canonical!r}.",
            )
        if not description.strip() or re.fullmatch(r"(?:activity|action|process|step|\d+)", description.strip(), re.I):
            add(
                findings,
                "HOUSE-ACT-004",
                "warning",
                "House",
                relative,
                f"DisplayName {display!r} needs a specific action description.",
            )
    duplicates = sorted(name for name, count in Counter(item.casefold() for item in names).items() if count > 1)
    for duplicate in duplicates:
        originals = sorted({name for name in names if name.casefold() == duplicate})
        add(
            findings,
            "HOUSE-ACT-002",
            "error",
            "House",
            relative,
            f"Activity DisplayName is not unique: {', '.join(originals)}.",
        )


def _audit_contracts(
    root: ET.Element,
    relative: str,
    findings: list[Finding],
) -> set[str]:
    arguments: list[tuple[str, str]] = []
    variables: list[tuple[str, str]] = []
    for element in root.iter():
        name = local_name(element.tag)
        if name == "Property":
            identifier = attribute(element, "Name") or ""
            type_value = attribute(element, "Type") or ""
            if identifier and type_value:
                arguments.append((identifier, type_value))
        elif name == "Variable":
            identifier = attribute(element, "Name") or ""
            type_value = attribute(element, "TypeArguments") or ""
            if identifier:
                variables.append((identifier, type_value))

    argument_count = len(arguments)
    if argument_count > 20:
        add(
            findings,
            "HOUSE-ARG-004",
            "error",
            "House",
            relative,
            f"Workflow has {argument_count} arguments; more than 20 requires a waiver.",
        )
    elif argument_count > 10:
        add(
            findings,
            "HOUSE-ARG-003",
            "warning",
            "House",
            relative,
            f"Workflow has {argument_count} arguments; review the interface before reaching UiPath's default threshold of 20.",
        )

    for identifier, type_value in arguments:
        direction, inner_type = direction_and_type(type_value)
        prefix = expected_type_prefix(inner_type)
        if direction is None:
            add(
                findings,
                "HOUSE-ARG-001",
                "error",
                "House",
                relative,
                f"Argument {identifier!r} has an unrecognized direction/type contract {type_value!r}.",
            )
        elif prefix and not identifier.startswith(direction + prefix):
            add(
                findings,
                "HOUSE-ARG-001",
                "error",
                "House",
                relative,
                f"Argument {identifier!r} must begin with {direction + prefix!r} for {inner_type}.",
            )
        if len(identifier) > 30:
            add(
                findings,
                "UIPATH-NMG-016",
                "warning",
                "UiPath",
                relative,
                f"Argument {identifier!r} is {len(identifier)} characters; UiPath's default Analyzer threshold is 30.",
            )
        if "genericvalue" in inner_type.casefold():
            add(
                findings,
                "HOUSE-TYPE-001",
                "error",
                "House",
                relative,
                f"Argument {identifier!r} uses GenericValue instead of a strong type.",
            )
        if inner_type.casefold() in {"object", "system.object", "x:object"}:
            add(
                findings,
                "HOUSE-TYPE-002",
                "warning",
                "House",
                relative,
                f"Argument {identifier!r} uses Object; confirm this is a cohesive typed contract.",
            )
        logical = identifier
        if direction and logical.startswith(direction):
            logical = logical[len(direction) :]
        if prefix and logical.startswith(prefix):
            logical = logical[len(prefix) :].lstrip("_")
        if logical.casefold() in {"data", "item", "result", "value"}:
            add(
                findings,
                "HOUSE-ARG-005",
                "warning",
                "House",
                relative,
                f"Argument {identifier!r} uses a generic logical name.",
            )
        if prefix == "bn" and re.search(r"(?:Not|No|Invalid|Disabled|False|Missing|Failed)", logical):
            add(
                findings,
                "HOUSE-ARG-006",
                "warning",
                "House",
                relative,
                f"Boolean argument {identifier!r} is negatively phrased; prefer a positive condition.",
            )

    variable_names = [identifier for identifier, _type in variables]
    for duplicate, count in Counter(item.casefold() for item in variable_names).items():
        if count > 1:
            originals = sorted({item for item in variable_names if item.casefold() == duplicate})
            add(
                findings,
                "HOUSE-VAR-002",
                "error",
                "House",
                relative,
                f"Variable name is duplicated or shadowed: {', '.join(originals)}.",
            )
    for identifier, type_value in variables:
        prefix = expected_type_prefix(type_value)
        if prefix and not identifier.startswith(prefix):
            add(
                findings,
                "HOUSE-VAR-001",
                "error",
                "House",
                relative,
                f"Variable {identifier!r} must begin with {prefix!r} for {type_value}.",
            )
        if len(identifier) > 30:
            add(
                findings,
                "UIPATH-NMG-008",
                "warning",
                "UiPath",
                relative,
                f"Variable {identifier!r} is {len(identifier)} characters; UiPath's default Analyzer threshold is 30.",
            )
        if "genericvalue" in type_value.casefold():
            add(
                findings,
                "HOUSE-TYPE-001",
                "error",
                "House",
                relative,
                f"Variable {identifier!r} uses GenericValue instead of a strong type.",
            )
        logical = identifier
        if prefix and logical.startswith(prefix):
            logical = logical[len(prefix) :].lstrip("_")
        if logical.casefold() in {"data", "item", "result", "value"}:
            add(
                findings,
                "HOUSE-VAR-003",
                "warning",
                "House",
                relative,
                f"Variable {identifier!r} uses a generic logical name.",
            )
        if prefix == "bn" and re.search(r"(?:Not|No|Invalid|Disabled|False|Missing|Failed)", logical):
            add(
                findings,
                "HOUSE-VAR-004",
                "warning",
                "House",
                relative,
                f"Boolean {identifier!r} is negatively phrased; prefer a positive condition.",
            )
    return {identifier for identifier, _type in arguments + variables}


def _activity_depths(
    activities: Sequence[ET.Element],
    parents: dict[ET.Element, ET.Element],
) -> tuple[int, int]:
    activity_set = set(activities)
    max_depth = 0
    max_if = 0
    for activity in activities:
        current: ET.Element | None = activity
        depth = 0
        if_count = 0
        while current is not None:
            if current in activity_set:
                depth += 1
                if local_name(current.tag) == "If":
                    if_count += 1
            current = parents.get(current)
        max_depth = max(max_depth, depth)
        max_if = max(max_if, if_count)
    return max_depth, max_if


def _is_boundary_log(element: ET.Element, stem: str, boundary: str) -> bool:
    expected_name = f"Log Message - {boundary.lower()} process"
    display = (attribute(element, "DisplayName") or "").casefold()
    expression = expression_for_log(element)
    pattern = rf"{boundary}:\s*{re.escape(stem)}\s*\|\s*\S+"
    return display == expected_name.casefold() and re.search(pattern, expression, re.I) is not None


def _audit_boundary_logs(
    root_visual: ET.Element,
    relative: str,
    stem: str,
    findings: list[Finding],
) -> None:
    root_name = local_name(root_visual.tag)
    if root_name == "Sequence":
        children = immediate_activities(root_visual)
        if not children or local_name(children[0].tag) != "LogMessage" or not _is_boundary_log(children[0], stem, "Start"):
            add(
                findings,
                "HOUSE-LOG-001",
                "error",
                "House",
                relative,
                f"First executable activity must be 'Log Message - Start process' with 'Start: {stem} | <concise purpose>'.",
            )
        if not children or local_name(children[-1].tag) != "LogMessage" or not _is_boundary_log(children[-1], stem, "End"):
            add(
                findings,
                "HOUSE-LOG-002",
                "error",
                "House",
                relative,
                f"Last successful activity must be 'Log Message - End process' with 'End: {stem} | <concise purpose>'.",
            )
        for boundary, position in (("Start", 0), ("End", -1)):
            if children and local_name(children[position].tag) == "LogMessage" and _is_boundary_log(children[position], stem, boundary):
                if log_level(children[position]).casefold() != "info":
                    add(
                        findings,
                        "HOUSE-LOG-017",
                        "error",
                        "House",
                        relative,
                        f"{boundary} boundary log must use Info level.",
                    )
        return
    logs = [element for element in root_visual.iter() if local_name(element.tag) == "LogMessage"]
    if not any(_is_boundary_log(log, stem, "Start") for log in logs):
        add(findings, "HOUSE-LOG-001", "error", "House", relative, "State/flow root has no exact Start boundary log.")
    if not any(_is_boundary_log(log, stem, "End") for log in logs):
        add(findings, "HOUSE-LOG-002", "error", "House", relative, "State/flow root has no exact End boundary log.")
    add(
        findings,
        "LINT-LIMIT-001",
        "info",
        "House",
        relative,
        f"{root_name} path ordering requires manual review; the linter verified boundary presence only.",
    )


def _audit_log_text(
    logs: Sequence[ET.Element],
    relative: str,
    stem: str,
    identifiers: set[str],
    config: StyleConfig,
    findings: list[Finding],
) -> None:
    for log in logs:
        expression = expression_for_log(log)
        display = attribute(log, "DisplayName") or "Log Message"
        is_boundary = _is_boundary_log(log, stem, "Start") or _is_boundary_log(log, stem, "End")
        banned = []
        patterns = {
            "Assigned:": r"\bAssigned\s*:",
            "Source=": r"\bSource\s*=",
            "Value=": r"\bValue\s*=",
            "PHI wording": r"\bPHI\b|PHI\s*=",
            "disclosure wording": r"\b(?:intentionally\s+)?(?:hidden|omitted|redacted)\b",
        }
        for label, pattern in patterns.items():
            if re.search(pattern, expression, re.I):
                banned.append(label)
        if banned:
            add(
                findings,
                "HOUSE-LOG-005",
                "error",
                "House",
                relative,
                f"{display!r} uses non-natural or disclosure-signaling wording: {', '.join(banned)}.",
            )
        if not is_boundary and "|" in expression:
            add(
                findings,
                "HOUSE-LOG-006",
                "warning",
                "House",
                relative,
                f"{display!r} uses a pipe outside the Start/End boundary delimiter.",
            )
        if re.search(r"\{\s*['\"]?\w+['\"]?\s*:", expression) or re.search(r"(?m)^\s*\w+\s*:\s*\w+", expression):
            add(
                findings,
                "HOUSE-LOG-007",
                "warning",
                "House",
                relative,
                f"{display!r} appears to use JSON/YAML-style fields instead of a natural sentence.",
            )
        outside = strip_string_literals(expression)
        for identifier in sorted(identifiers):
            if (
                value_classification(identifier, config) == "sensitive"
                and contains_identifier(outside, identifier)
            ):
                add(
                    findings,
                    "SEC-LOG-001",
                    "error",
                    "Security",
                    relative,
                    f"{display!r} dynamically interpolates sensitive or unclassified identifier {identifier!r}.",
                    "Keep the variable name in the sentence but remove the runtime value reference.",
                )
        if re.search(r"\b(?:ex\w*|exception)\s*\.\s*(?:Message|StackTrace|ToString)\b", outside, re.I):
            add(
                findings,
                "SEC-LOG-003",
                "error",
                "Security",
                relative,
                f"{display!r} interpolates raw exception content.",
            )


def _audit_assignment_log(
    activity: ET.Element,
    log: ET.Element,
    relative: str,
    config: StyleConfig,
    findings: list[Finding],
) -> None:
    pairs = assignment_pairs(activity)
    targets = [target for target, _value in pairs]
    activity_name = local_name(activity.tag)
    expression = expression_for_log(log)
    outside = strip_string_literals(expression)
    if not targets:
        add(
            findings,
            "HOUSE-LOG-008",
            "warning",
            "House",
            relative,
            f"Could not statically resolve the target of {attribute(activity, 'DisplayName') or activity_name!r}.",
        )
        return
    if activity_name == "MultipleAssign":
        if len(targets) < 2:
            add(findings, "HOUSE-WF-007", "warning", "House", relative, "Multiple Assign contains fewer than two resolved assignments.")
        if len(targets) > 10:
            add(
                findings,
                "HOUSE-WF-007",
                "warning",
                "House",
                relative,
                f"Multiple Assign contains {len(targets)} operations; split groups larger than 10.",
            )
        newline_count = len(
            re.findall(r"Environment\.NewLine|vbCrLf|vbLf|ChrW?\s*\(\s*10\s*\)", expression, re.I)
        )
        if len(targets) > 1 and newline_count < len(targets) - 1:
            add(
                findings,
                "HOUSE-LOG-009",
                "error",
                "House",
                relative,
                f"Multiple Assign log needs one newline-separated sentence per assignment ({len(targets)} targets).",
            )
    for target in targets:
        if not contains_identifier(expression, target):
            add(
                findings,
                "HOUSE-LOG-010",
                "error",
                "House",
                relative,
                f"Assignment log does not name target variable {target!r} exactly.",
            )
            continue
        dynamic = contains_identifier(outside, target)
        classification = value_classification(target, config)
        if classification == "safe" and not dynamic:
            add(
                findings,
                "HOUSE-LOG-011",
                "error",
                "House",
                relative,
                f"Approved safe target {target!r} is not dynamically referenced in its assignment log.",
                f"Concatenate {target} at runtime instead of typing an expected value.",
            )
    for target, value in pairs:
        literal = literal_assignment(value)
        if literal is None:
            continue
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(literal)}(?![A-Za-z0-9_])", expression, re.I):
            classification = value_classification(target, config)
            add(
                findings,
                "SEC-LOG-002" if classification == "sensitive" else "HOUSE-LOG-018",
                "error",
                "Security" if classification == "sensitive" else "House",
                relative,
                f"Assignment log copies literal {literal!r} for target {target!r} instead of following the value-handling rule.",
                (
                    "Name the target without its value."
                    if classification == "sensitive"
                    else f"Concatenate {target} after assignment."
                ),
            )


def _branch_first_log(
    decision: ET.Element,
    relative: str,
    findings: list[Finding],
) -> None:
    name = local_name(decision.tag)
    if name == "If":
        branch_nodes = [child for child in decision if local_name(child.tag).split(".")[-1] in {"Then", "Else"}]
    else:
        branch_nodes = immediate_activities(decision)
    for branch in branch_nodes:
        first = first_executable(branch)
        branch_name = (
            local_name(branch.tag).split(".")[-1]
            if name == "If"
            else attribute(branch, "DisplayName") or attribute(branch, "Key") or canonical_activity_name(name)
        )
        if first is None or local_name(first.tag) != "LogMessage":
            add(
                findings,
                "HOUSE-LOG-012",
                "error",
                "House",
                relative,
                f"{canonical_activity_name(name)} branch {branch_name!r} must begin with a contextual Log Message for the selected result.",
            )


def _is_important_loop_log(expression: str) -> bool:
    return re.search(
        r"\b(?:attempt|completed|created|deleted|failed|retry|saved|selected|submitted|updated|warn)\w*\b",
        expression,
        re.I,
    ) is not None


def _audit_sequence_adjacency(
    root: ET.Element,
    relative: str,
    stem: str,
    config: StyleConfig,
    findings: list[Finding],
) -> None:
    parents = _parent_map(root)
    for sequence in (element for element in root.iter() if local_name(element.tag) == "Sequence"):
        children = immediate_activities(sequence)
        for index, activity in enumerate(children):
            name = local_name(activity.tag)
            previous = children[index - 1] if index else None
            following = children[index + 1] if index + 1 < len(children) else None
            if name == "LogMessage" or name in PASSIVE_CONTAINERS:
                continue
            if name == "InvokeWorkflowFile":
                if (
                    following is not None
                    and local_name(following.tag) == "LogMessage"
                    and not _is_boundary_log(following, stem, "End")
                ):
                    add(
                        findings,
                        "HOUSE-LOG-013",
                        "error",
                        "House",
                        relative,
                        "Caller-side Log Message immediately follows Invoke Workflow File; rely on the child boundary logs.",
                    )
                continue
            if name in TERMINATORS:
                if previous is None or local_name(previous.tag) != "LogMessage" or _is_boundary_log(previous, stem, "Start"):
                    add(
                        findings,
                        "HOUSE-LOG-004",
                        "error",
                        "House",
                        relative,
                        f"{canonical_activity_name(name)} needs its contextual log immediately before the terminating action.",
                    )
                continue
            if name in DECISIONS:
                _branch_first_log(activity, relative, findings)
                continue
            if name in LOOPS:
                if previous is None or local_name(previous.tag) != "LogMessage" or _is_boundary_log(previous, stem, "Start"):
                    add(
                        findings,
                        "HOUSE-LOG-014",
                        "error",
                        "House",
                        relative,
                        f"{canonical_activity_name(name)} needs a dedicated Info Start log immediately before the loop.",
                    )
                if following is None or local_name(following.tag) != "LogMessage" or _is_boundary_log(following, stem, "End"):
                    add(
                        findings,
                        "HOUSE-LOG-015",
                        "error",
                        "House",
                        relative,
                        f"{canonical_activity_name(name)} needs a dedicated Info End log immediately after the loop.",
                    )
                for label, adjacent in (("Start", previous), ("End", following)):
                    if adjacent is not None and local_name(adjacent.tag) == "LogMessage" and not _is_boundary_log(adjacent, stem, label):
                        if log_level(adjacent).casefold() != "info":
                            add(
                                findings,
                                "HOUSE-LOG-017",
                                "error",
                                "House",
                                relative,
                                f"Dedicated loop {label} log must use Info level.",
                            )
                continue
            if following is None or local_name(following.tag) != "LogMessage":
                add(
                    findings,
                    "HOUSE-LOG-003",
                    "error",
                    "House",
                    relative,
                    f"{attribute(activity, 'DisplayName') or canonical_activity_name(name)!r} is not immediately followed by a contextual Log Message.",
                )
                continue
            if _is_boundary_log(following, stem, "End"):
                add(
                    findings,
                    "HOUSE-LOG-003",
                    "error",
                    "House",
                    relative,
                    f"{attribute(activity, 'DisplayName') or canonical_activity_name(name)!r} needs an action-result log before the workflow End boundary.",
                )
                continue
            if name in {"Assign", "MultipleAssign"}:
                _audit_assignment_log(activity, following, relative, config, findings)

    for log in (element for element in root.iter() if local_name(element.tag) == "LogMessage"):
        ancestor = parents.get(log)
        loop: ET.Element | None = None
        while ancestor is not None:
            if local_name(ancestor.tag) in LOOPS:
                loop = ancestor
                break
            ancestor = parents.get(ancestor)
        if loop is None:
            continue
        loop_name = local_name(loop.tag)
        loop_text = element_text(loop)
        count_match = re.search(r"Enumerable\.Range\s*\([^,]+,\s*(\d+)\s*\)", loop_text, re.I)
        bounded_small = bool(count_match and int(count_match.group(1)) <= config.loop_threshold)
        if not bounded_small and log_level(log).casefold() == "info" and not _is_important_loop_log(expression_for_log(log)):
            add(
                findings,
                "HOUSE-LOG-016",
                "warning",
                "House",
                relative,
                f"Routine Info log inside {canonical_activity_name(loop_name)} may flood runs above {config.loop_threshold} iterations; use Trace unless consequential.",
            )


def _audit_risk_activities(
    root: ET.Element,
    activities: Sequence[ET.Element],
    parents: dict[ET.Element, ET.Element],
    relative: str,
    findings: list[Finding],
) -> None:
    ui_markers = re.compile(r"(?:Click|TypeInto|UseApplicationBrowser|SendControlKey|CheckAppState|GetText|SetText)$")
    for activity in activities:
        name = local_name(activity.tag)
        if name in {"InvokeCode", "InvokeMethod"}:
            add(
                findings,
                "HOUSE-CODE-001",
                "error",
                "House",
                relative,
                f"{canonical_activity_name(name)} is prohibited by default; use a native activity or record a scoped waiver.",
            )
        if name == "WriteLine":
            add(
                findings,
                "UIPATH-MRD-011",
                "warning",
                "UiPath",
                relative,
                "Write Line remains in a governed workflow; replace a durable diagnostic with Log Message.",
            )
        continue_on_error = attribute(activity, "ContinueOnError")
        if continue_on_error and re.search(r"\bTrue\b", continue_on_error, re.I):
            add(
                findings,
                "HOUSE-ERR-001",
                "error",
                "House",
                relative,
                f"{attribute(activity, 'DisplayName') or canonical_activity_name(name)!r} sets ContinueOnError=True.",
            )
        if ui_markers.search(name):
            ancestor = parents.get(activity)
            while ancestor is not None:
                if local_name(ancestor.tag) == "Parallel":
                    add(
                        findings,
                        "UIPATH-UI-001",
                        "error",
                        "UiPath",
                        relative,
                        f"UI Automation activity {canonical_activity_name(name)!r} is inside Parallel, which UiPath documents as unsupported.",
                    )
                    break
                ancestor = parents.get(ancestor)
        if name == "Delay":
            if any(
                ui_markers.search(local_name(item.tag))
                for item in root.iter()
                if item is not activity
            ):
                add(
                    findings,
                    "HOUSE-UI-002",
                    "warning",
                    "House",
                    relative,
                    "Delay appears in a UI workflow; confirm state checks and bounded timeouts are the primary synchronization.",
                )
    for catch in (element for element in root.iter() if local_name(element.tag) == "Catch"):
        meaningful = [
            item
            for item in catch.iter()
            if is_activity(item) and local_name(item.tag) not in PASSIVE_CONTAINERS
        ]
        if not meaningful:
            add(
                findings,
                "UIPATH-DBP-003",
                "error",
                "UiPath",
                relative,
                "Catch block is empty and appears to swallow an exception.",
            )


def audit_workflow(
    path: Path,
    project: Path,
    config: StyleConfig,
    collisions: dict[str, list[str]],
) -> tuple[list[Finding], str | None]:
    relative = relative_path(path, project)
    findings: list[Finding] = []
    _audit_filename(path, relative, config, collisions, findings)
    try:
        source = path.read_text(encoding="utf-8-sig")
        root = ET.fromstring(source)
    except (OSError, UnicodeError, ET.ParseError) as exc:
        return findings, f"{relative}: XML parse failed: {exc}"

    root_visual = find_root_visual(root)
    if root_visual is None:
        add(findings, "HOUSE-ROOT-001", "error", "House", relative, "No Sequence, Flowchart, or State Machine root was found.")
        return findings, None
    root_display = attribute(root_visual, "DisplayName") or ""
    if root_display != path.stem:
        add(
            findings,
            "HOUSE-ROOT-002",
            "error",
            "House",
            relative,
            f"Root DisplayName {root_display!r} must exactly equal filename stem {path.stem!r}.",
        )
    _audit_annotation(root_visual, relative, findings)

    activities = [element for element in root.iter() if is_activity(element)]
    parents = _parent_map(root)
    maximum_depth, nested_if = _activity_depths(activities, parents)
    count = sum(1 for element in root.iter() if is_size_activity(element))
    size = path.stat().st_size
    if count > 55:
        add(
            findings,
            "HOUSE-WF-006",
            "error",
            "House",
            relative,
            f"Workflow contains approximately {count} activities; more than 55 requires a modularity waiver.",
        )
    elif count > 50:
        add(
            findings,
            "HOUSE-WF-005",
            "warning",
            "House",
            relative,
            f"Workflow contains approximately {count} activities; perform the 51–55 modularity review.",
        )
    if size > 10 * 1024 * 1024:
        add(findings, "UIPATH-WF-002", "error", "UiPath", relative, f"Workflow is {size} bytes; files above 10 MB are unsupported.")
    elif size > 5 * 1024 * 1024:
        add(findings, "UIPATH-WF-001", "warning", "UiPath", relative, f"Workflow is {size} bytes; UiPath recommends keeping workflows below 5 MB.")
    if maximum_depth >= 7:
        add(
            findings,
            "UIPATH-MRD-009",
            "warning",
            "UiPath",
            relative,
            f"Approximate activity nesting depth is {maximum_depth}; UiPath's default review threshold is seven.",
        )
    if nested_if > 3:
        add(
            findings,
            "UIPATH-MRD-007",
            "warning",
            "UiPath",
            relative,
            f"Detected {nested_if} nested If activities; UiPath recommends avoiding more than three.",
        )

    _audit_activity_names(activities, root_visual, relative, findings)
    identifiers = _audit_contracts(root, relative, findings)
    _audit_boundary_logs(root_visual, relative, path.stem, findings)
    logs = [element for element in activities if local_name(element.tag) == "LogMessage"]
    _audit_log_text(logs, relative, path.stem, identifiers, config, findings)
    _audit_sequence_adjacency(root, relative, path.stem, config, findings)
    _audit_risk_activities(root, activities, parents, relative, findings)
    argument_count = sum(1 for element in root.iter() if local_name(element.tag) == "Property")
    variable_count = sum(1 for element in root.iter() if local_name(element.tag) == "Variable")
    add(
        findings,
        "METRIC-WF-001",
        "info",
        "House",
        relative,
        f"Static metrics: activities≈{count}, arguments={argument_count}, variables={variable_count}, nesting≈{maximum_depth}, bytes={size}.",
    )
    return findings, None


def apply_waivers(findings: Iterable[Finding], config: StyleConfig) -> list[Finding]:
    result: list[Finding] = []
    for finding in findings:
        if finding.severity == "info" or finding.source == "Security" or finding.rule in NON_WAIVABLE_RULES:
            result.append(finding)
            continue
        waiver = next(
            (
                item
                for item in config.waivers
                if item.active
                and fnmatch.fnmatchcase(finding.rule, item.rule)
                and fnmatch.fnmatchcase(finding.path, item.workflow)
            ),
            None,
        )
        if waiver is None:
            result.append(finding)
            continue
        result.append(
            Finding(
                rule=finding.rule,
                severity="info",
                source=finding.source,
                path=finding.path,
                message=(
                    f"Waived {finding.severity}: {finding.message} "
                    f"Rationale: {waiver.rationale} Approver: {waiver.approver}. "
                    f"Expires: {waiver.expiration.isoformat()}."
                ),
                suggestion=finding.suggestion,
                waived=True,
                original_severity=finding.severity,
            )
        )
    return result


def audit_project(
    project: Path,
    scope: str = "all",
    selected: Sequence[str] = (),
    config_path: Path | None = None,
) -> AuditResult:
    project = project.resolve()
    if not project.is_dir():
        raise ConfigurationError(f"Project directory does not exist: {project}")
    config = load_config(project, config_path)
    selected_paths = resolve_scope(project, scope, selected)
    all_files = all_xaml_files(project)
    collisions: dict[str, list[str]] = {}
    for path in all_files:
        relative = relative_path(path, project)
        if Path(relative).name.startswith("TC_"):
            continue
        collisions.setdefault(path.name.casefold(), []).append(relative)

    files: list[str] = []
    findings: list[Finding] = []
    errors: list[str] = []
    for path in selected_paths:
        relative = relative_path(path, project)
        if is_generated(path, project) or is_protected(relative, config):
            continue
        files.append(relative)
        workflow_findings, error = audit_workflow(path, project, config, collisions)
        findings.extend(workflow_findings)
        if error:
            errors.append(error)

    for waiver in config.waivers:
        if not waiver.active:
            add(
                findings,
                "CFG-WAIVER-001",
                "warning",
                "House",
                waiver.workflow,
                f"Waiver for {waiver.rule} expired on {waiver.expiration.isoformat()} and no longer suppresses findings.",
            )
    return AuditResult(project, scope, files, apply_waivers(findings, config), errors)


def exit_code(result: AuditResult, fail_on: str) -> int:
    if result.operational_errors:
        return 2
    if any(item.severity == "error" for item in result.findings):
        return 1
    if fail_on == "warning" and any(item.severity == "warning" for item in result.findings):
        return 1
    return 0


def print_text(result: AuditResult, code: int) -> None:
    for error in result.operational_errors:
        print(f"PARSE ERROR {error}")
    for finding in result.sorted_findings():
        print(f"{finding.severity.upper():7} {finding.rule:18} [{finding.source}] {finding.path}: {finding.message}")
        if finding.suggestion:
            print(f"         suggestion: {finding.suggestion}")
    counts = result.counts()
    print(
        f"Summary: files={len(result.files)} errors={counts['error']} warnings={counts['warning']} "
        f"info={counts['info']} parse_errors={len(result.operational_errors)} exit={code}"
    )
    print("Boundary: read-only XML heuristics only; Windows Studio validation, build, Robot execution, and UAT remain separate.")


def print_json(result: AuditResult, code: int) -> None:
    payload = {
        "schema": SCHEMA,
        "tool_version": TOOL_VERSION,
        "project": str(result.project),
        "scope": result.scope,
        "files": result.files,
        "findings": [item.to_dict() for item in result.sorted_findings()],
        "operational_errors": result.operational_errors,
        "summary": {**result.counts(), "parse_errors": len(result.operational_errors), "exit_code": code},
        "validation_boundary": "Read-only XML heuristics; not Studio validation, build, execution, or UAT.",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="UiPath project root (default: current directory).")
    parser.add_argument("--scope", choices=("all", "changed", "selected"), default="all")
    parser.add_argument("--files", nargs="*", default=(), help="Project-relative XAML paths for --scope selected.")
    parser.add_argument("--config", type=Path, help="Optional configuration path; defaults to PROJECT/.uipath-style.json.")
    parser.add_argument("--format", choices=("text", "json"), default="text", dest="output_format")
    parser.add_argument("--fail-on", choices=("error", "warning"), default="error")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = audit_project(args.project, args.scope, args.files, args.config)
    except ConfigurationError as exc:
        if args.output_format == "json":
            print(
                json.dumps(
                    {
                        "schema": SCHEMA,
                        "tool_version": TOOL_VERSION,
                        "operational_errors": [str(exc)],
                        "summary": {"error": 0, "warning": 0, "info": 0, "parse_errors": 1, "exit_code": 2},
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(f"CONFIG ERROR: {exc}", file=sys.stderr)
        return 2
    code = exit_code(result, args.fail_on)
    if args.output_format == "json":
        print_json(result, code)
    else:
        print_text(result, code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
