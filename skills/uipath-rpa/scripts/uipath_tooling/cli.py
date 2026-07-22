from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .contracts import validate_contracts
from .discovery import (
    ProjectDiscoveryError,
    all_xaml,
    load_project_json,
    relative,
    resolve_project_root,
    scoped_xaml,
)
from .expressions import check_workflow
from .line_endings import check as check_line_endings
from .line_endings import normalize as normalize_line_endings
from .metadata import validate_metadata
from .policies import PolicyError, load_policy, validate_policy
from .project_model import Finding, now_iso
from .reporting import text_report, validation_result, write_json
from .runners.parallels import ParallelsRunner, new_request
from .workflow_graph import dumps as map_json
from .workflow_graph import mermaid, project_map
from .xaml_parser import duplicate_id_refs, parse_workflow, serialization_findings


SKILL_ROOT = Path(__file__).resolve().parents[2]


def _project_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project", required=True, help="UiPath project directory or a path below it"
    )


def _scope_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--scope", choices=("all", "changed", "staged"), default="changed"
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
        help="Explicit XAML paths, relative to the project",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="uipath_tool.py",
        description="Inspect and validate UiPath projects deterministically",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subcommands.add_parser(
        "inspect", help="Map workflows, contracts, and complexity"
    )
    _project_argument(inspect_parser)
    inspect_parser.add_argument(
        "--entry", default=None, help="Entry workflow to emphasize"
    )
    inspect_parser.add_argument(
        "--format", choices=("text", "json", "mermaid"), default="text"
    )
    inspect_parser.add_argument("--out", type=Path)

    audit_parser = subcommands.add_parser(
        "audit", help="Run the L1 static validation gate"
    )
    _project_argument(audit_parser)
    _scope_arguments(audit_parser)
    audit_parser.add_argument("--policy", default="baseline")
    audit_parser.add_argument(
        "--require-registered-tests",
        action="store_true",
        help="Treat every unregistered TC_*.xaml workflow as an L1 error",
    )
    audit_parser.add_argument("--format", choices=("text", "json"), default="text")
    audit_parser.add_argument("--json-out", type=Path)

    eol_parser = subcommands.add_parser(
        "normalize-eol", help="Check or repair XAML line endings"
    )
    _project_argument(eol_parser)
    _scope_arguments(eol_parser)
    mode = eol_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")

    windows_parser = subcommands.add_parser(
        "windows", help="Use the local Windows validation bridge"
    )
    windows_commands = windows_parser.add_subparsers(
        dest="windows_command", required=True
    )
    preflight = windows_commands.add_parser(
        "preflight", help="Check Parallels and the Windows UiPath toolchain"
    )
    preflight.add_argument(
        "--vm", default=os.environ.get("UIPATH_PARALLELS_VM", "Windows 11")
    )
    preflight.add_argument("--format", choices=("text", "json"), default="text")
    validate = windows_commands.add_parser(
        "validate", help="Build and optionally execute a project in Windows"
    )
    _project_argument(validate)
    validate.add_argument(
        "--vm", default=os.environ.get("UIPATH_PARALLELS_VM", "Windows 11")
    )
    validate.add_argument(
        "--mode", choices=("build", "build-and-test", "run-workflow"), default="build"
    )
    validate.add_argument(
        "--tests", choices=("changed", "all", "paths"), default="changed"
    )
    validate.add_argument("--test-path", action="append", default=[])
    validate.add_argument("--allow-side-effects", action="store_true")
    validate.add_argument("--keep-job", action="store_true")
    validate.add_argument("--json-out", type=Path)

    result_parser = subcommands.add_parser(
        "result", help="Work with a validation result"
    )
    result_commands = result_parser.add_subparsers(dest="result_command", required=True)
    explain = result_commands.add_parser(
        "explain", help="Explain a validation-result JSON file"
    )
    explain.add_argument("path", type=Path)
    return parser


def _parse_workflows(project_root: Path) -> tuple[dict[str, Any], list[Finding]]:
    workflows = {}
    findings: list[Finding] = []
    for path in all_xaml(project_root):
        relative_path = relative(project_root, path)
        try:
            workflows[relative_path] = parse_workflow(path, project_root)
        except (ET.ParseError, UnicodeDecodeError, OSError) as error:
            findings.append(
                Finding("XML001", "error", f"XAML parse failed: {error}", relative_path)
            )
    return workflows, findings


def _git_diff_findings(project_root: Path) -> list[Finding]:
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(project_root),
                "-c",
                "core.whitespace=cr-at-eol",
                "diff",
                "--check",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if completed.returncode == 0:
        return []
    return [
        Finding(
            "GIT001",
            "error",
            line,
            remediation="Resolve the diff-check finding without converting intentional CRLF XAML.",
        )
        for line in completed.stdout.splitlines()
        if line
    ]


def run_inspect(args: argparse.Namespace) -> int:
    project_root = resolve_project_root(args.project)
    project = load_project_json(project_root)
    workflows, findings = _parse_workflows(project_root)
    data = project_map(project, workflows, project_root)
    if findings:
        data["findings"] = [finding.to_dict() for finding in findings]
    if args.entry:
        data["requested_entry"] = args.entry.replace("\\", "/")
    if args.format == "json":
        output = map_json(data)
    elif args.format == "mermaid":
        output = mermaid(data)
    else:
        output = _map_text(data)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if findings else 0


def _map_text(data: dict[str, Any]) -> str:
    project = data["project"]
    lines = [
        f"UiPath project map: {project.get('name')}",
        f"Target: {project.get('target_framework')} · Language: {project.get('expression_language')}",
        f"Workflows: {len(data['nodes'])} · Invoke edges: {len(data['edges'])}",
        "",
    ]
    for node in sorted(
        data["nodes"], key=lambda value: (-value["activities"], value["path"])
    ):
        flags = []
        if node["invoke_code"]:
            flags.append(f"InvokeCode={node['invoke_code']}")
        if node["invoke_method"]:
            flags.append(f"InvokeMethod={node['invoke_method']}")
        suffix = f" · {' · '.join(flags)}" if flags else ""
        lines.append(
            f"{node['path']} — {node['activities']} activities, {node['variables']} variables, {node['invokes']} invokes, depth {node['max_depth']}{suffix}"
        )
        if node.get("argument_contracts"):
            contracts = "; ".join(
                f"{item['name']} {item['direction']} {item['type']}"
                for item in node["argument_contracts"]
            )
            lines.append(f"  Arguments: {contracts}")
    findings = data.get("findings", [])
    if findings:
        lines.extend(("", "Inspection findings:"))
        for finding in findings:
            location = f" ({finding['file']})" if finding.get("file") else ""
            lines.append(
                f"[{finding['severity'].upper()}] {finding['code']}{location}: {finding['message']}"
            )
    return "\n".join(lines)


def run_audit(args: argparse.Namespace) -> int:
    started = now_iso()
    project_root = resolve_project_root(args.project)
    project = load_project_json(project_root)
    policy = load_policy(SKILL_ROOT, args.policy)
    scoped_paths = scoped_xaml(project_root, args.scope, args.files)
    scoped = {relative(project_root, path) for path in scoped_paths}
    workflows, findings = _parse_workflows(project_root)
    if not scoped_paths:
        findings.append(
            Finding(
                "SCP001",
                "error",
                "The selected scope contains no XAML workflows.",
                remediation="Use --files for the intended workflows or choose a scope that contains XAML changes.",
            )
        )
    for path in scoped_paths:
        relative_path = relative(project_root, path)
        workflow = workflows.get(relative_path)
        if workflow is None:
            continue
        for duplicate in duplicate_id_refs(workflow):
            findings.append(
                Finding(
                    "XML002",
                    "error",
                    f"Duplicate WorkflowViewState.IdRef: {duplicate}",
                    relative_path,
                )
            )
        findings.extend(check_workflow(workflow))
        findings.extend(validate_policy(workflow, policy))
        findings.extend(serialization_findings(project_root, workflow, workflows))
    findings.extend(check_line_endings(project_root, scoped_paths))
    findings.extend(validate_contracts(project_root, workflows, scoped))
    findings.extend(
        validate_metadata(
            project_root,
            project,
            require_registered_tests=args.require_registered_tests,
        )
    )
    findings.extend(_git_diff_findings(project_root))
    findings.sort(key=lambda item: (item.file or "", item.code, item.message))
    result = validation_result(project, findings, sorted(scoped), started)
    if args.json_out:
        write_json(args.json_out, result)
    print(
        json.dumps(result, indent=2) if args.format == "json" else text_report(result)
    )
    return 1 if result["gates"]["static"]["status"] == "failed" else 0


def run_eol(args: argparse.Namespace) -> int:
    project_root = resolve_project_root(args.project)
    paths = scoped_xaml(project_root, args.scope, args.files)
    changes = normalize_line_endings(project_root, paths, write=args.write)
    action = "normalized" if args.write else "would normalize"
    if changes:
        for change in changes:
            print(f"{change['file']}: {action} {change['from']} -> {change['to']}")
    else:
        print(
            f"Line endings already match the expected style for {len(paths)} file(s)."
        )
    return 0 if args.write or not changes else 1


def _preflight_text(value: dict[str, Any]) -> str:
    lines = [f"Parallels UiPath preflight: {value['status']} ({value['vm_name']})"]
    for check in value["checks"]:
        lines.append(
            f"[{check['status'].upper()}] {check['name']}: {check.get('detail') or ''}"
        )
        if check.get("remediation"):
            lines.append(f"  Remediation: {check['remediation']}")
    return "\n".join(lines)


def run_windows(args: argparse.Namespace) -> int:
    runner = ParallelsRunner(args.vm, SKILL_ROOT)
    if args.windows_command == "preflight":
        result = runner.preflight()
        print(
            json.dumps(result, indent=2)
            if args.format == "json"
            else _preflight_text(result)
        )
        return 0 if result["status"] == "passed" else 3
    project_root = resolve_project_root(args.project)
    test_paths = list(args.test_path)
    if args.tests == "changed" and not test_paths:
        project = load_project_json(project_root)
        registered = {
            str(item.get("fileName", "")).replace("\\", "/")
            for item in project.get("designOptions", {}).get("fileInfoCollection", [])
            or []
            if item.get("testCaseId")
        }
        test_paths = [
            relative(project_root, path)
            for path in scoped_xaml(project_root, "changed")
            if relative(project_root, path) in registered
        ]
    request = new_request(
        project_root,
        args.mode,
        args.tests,
        test_paths,
        args.allow_side_effects,
        args.keep_job,
    )
    exit_code, result = runner.validate(request)
    if args.json_out:
        write_json(args.json_out, result)
    print(text_report(result))
    return exit_code


def run_result(args: argparse.Namespace) -> int:
    try:
        result = json.loads(args.path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read validation result: {error}", file=sys.stderr)
        return 2
    print(text_report(result))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            return run_inspect(args)
        if args.command == "audit":
            return run_audit(args)
        if args.command == "normalize-eol":
            return run_eol(args)
        if args.command == "windows":
            return run_windows(args)
        if args.command == "result":
            return run_result(args)
    except (ProjectDiscoveryError, PolicyError, ValueError, OSError) as error:
        print(f"UiPath tooling error: {error}", file=sys.stderr)
        return 2
    return 2
