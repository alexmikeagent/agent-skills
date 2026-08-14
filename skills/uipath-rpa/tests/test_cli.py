from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(skill_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(skill_root / "scripts" / "uipath_tool.py"), *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_valid_fixture_passes_static_cli(
    valid_project: Path, skill_root: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.json"
    completed = _run(
        skill_root,
        "audit",
        "--project",
        str(valid_project),
        "--scope",
        "all",
        "--policy",
        "baseline",
        "--format",
        "json",
        "--json-out",
        str(output),
    )
    result = json.loads(output.read_text())
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert result["gates"]["static"]["status"] == "passed"
    assert result["gates"]["compile"]["status"] == "not_run"


def test_malformed_xaml_fails_static_cli(skill_root: Path) -> None:
    project = skill_root / "tests" / "fixtures" / "malformed-xaml"
    completed = _run(skill_root, "audit", "--project", str(project), "--scope", "all")
    assert completed.returncode == 1
    assert "XML001" in completed.stdout


def test_inspect_surfaces_malformed_xaml_in_text(skill_root: Path) -> None:
    project = skill_root / "tests" / "fixtures" / "malformed-xaml"
    completed = _run(
        skill_root, "inspect", "--project", str(project), "--format", "text"
    )
    assert completed.returncode == 1
    assert "Inspection findings:" in completed.stdout
    assert "[ERROR] XML001 (Main.xaml)" in completed.stdout
    assert "mismatched tag" in completed.stdout


def test_result_explain_uses_gate_language(
    valid_project: Path, skill_root: Path, tmp_path: Path
) -> None:
    output = tmp_path / "result.json"
    assert (
        _run(
            skill_root,
            "audit",
            "--project",
            str(valid_project),
            "--scope",
            "all",
            "--json-out",
            str(output),
        ).returncode
        == 0
    )
    explained = _run(skill_root, "result", "explain", str(output))
    assert explained.returncode == 0
    assert "L1 static: passed" in explained.stdout
    assert "L2 compile: not_run" in explained.stdout


def test_empty_changed_scope_is_not_a_vacuous_pass(
    valid_project: Path, skill_root: Path
) -> None:
    completed = _run(
        skill_root, "audit", "--project", str(valid_project), "--scope", "changed"
    )
    assert completed.returncode == 1
    assert "SCP001" in completed.stdout


def test_registration_gate_fails_unregistered_tests(
    valid_project: Path, skill_root: Path
) -> None:
    project_path = valid_project / "project.json"
    project = json.loads(project_path.read_text())
    project["designOptions"]["fileInfoCollection"] = []
    project_path.write_text(json.dumps(project, indent=2) + "\n")
    completed = _run(
        skill_root,
        "audit",
        "--project",
        str(valid_project),
        "--scope",
        "all",
        "--require-registered-tests",
    )
    assert completed.returncode == 1
    assert "[ERROR] META003" in completed.stdout


def test_csharp_project_skips_visual_basic_expression_heuristics(
    valid_project: Path, skill_root: Path
) -> None:
    project_path = valid_project / "project.json"
    project = json.loads(project_path.read_text())
    project["expressionLanguage"] = "CSharp"
    project_path.write_text(json.dumps(project, indent=2) + "\n")
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace("[1D]", '[Regex.IsMatch("x", "x") ? 1D : 0D]')
    )
    completed = _run(
        skill_root, "audit", "--project", str(valid_project), "--scope", "all"
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "VB003" not in completed.stdout


def test_unknown_expression_language_is_reported(
    valid_project: Path, skill_root: Path
) -> None:
    project_path = valid_project / "project.json"
    project = json.loads(project_path.read_text())
    project["expressionLanguage"] = "UnknownLanguage"
    project_path.write_text(json.dumps(project, indent=2) + "\n")
    completed = _run(
        skill_root, "audit", "--project", str(valid_project), "--scope", "all"
    )
    assert completed.returncode == 0
    assert "CFG001" in completed.stdout
