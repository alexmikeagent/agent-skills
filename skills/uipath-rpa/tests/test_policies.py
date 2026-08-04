from pathlib import Path

import pytest

from uipath_tooling.policies import PolicyError, load_policy, validate_policy
from uipath_tooling.xaml_parser import parse_workflow
from uipath_tooling.xaml_parser import naming_findings, serialization_findings


def test_native_policy_accepts_expanded_assign_and_story_log(
    valid_project: Path, skill_root: Path
) -> None:
    policy = load_policy(skill_root, "native-business-rules")
    workflow = parse_workflow(valid_project / "Main.xaml", valid_project)
    codes = {finding.code for finding in validate_policy(workflow, policy)}
    assert "POL001" not in codes
    assert "POL003" not in codes
    assert "POL004" not in codes
    assert "POL005" not in codes


def test_policy_detects_forbidden_activity(
    valid_project: Path, skill_root: Path
) -> None:
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace(
            "</Sequence>", '<ui:InvokeCode DisplayName="bad" /></Sequence>'
        ),
        encoding="utf-8",
    )
    workflow = parse_workflow(main, valid_project)
    findings = validate_policy(
        workflow, load_policy(skill_root, "native-business-rules")
    )
    assert "POL001" in {finding.code for finding in findings}


def test_unknown_policy_key_fails(tmp_path: Path, skill_root: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"schema":"uipath-policy/v1","mystery":true}')
    with pytest.raises(PolicyError):
        load_policy(skill_root, str(path))


def test_novel_activity_requires_windows_proof(valid_project: Path) -> None:
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace(
            "</Sequence>", '<ui:NovelActivity DisplayName="Novel" /></Sequence>'
        ),
        encoding="utf-8",
    )
    workflow = parse_workflow(main, valid_project)
    workflows = {"Main.xaml": workflow}
    findings = serialization_findings(valid_project, workflow, workflows)
    assert any(
        finding.code == "ACT001" and "NovelActivity" in finding.message
        for finding in findings
    )


def test_name_lengths_at_analyzer_default_are_accepted(valid_project: Path) -> None:
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace('Name="amount"', f'Name="{"v" * 30}"'),
        encoding="utf-8",
    )
    workflow = parse_workflow(main, valid_project)
    assert "ST-NMG-008" not in {
        finding.code for finding in naming_findings(workflow)
    }


def test_overlong_argument_and_variable_names_are_reported(
    valid_project: Path,
) -> None:
    child = valid_project / "Child.xaml"
    child.write_text(
        child.read_text().replace('Name="in_amount"', f'Name="{"a" * 31}"'),
        encoding="utf-8",
    )
    main = valid_project / "Main.xaml"
    main.write_text(
        main.read_text().replace('Name="amount"', f'Name="{"v" * 31}"'),
        encoding="utf-8",
    )
    findings = naming_findings(parse_workflow(child, valid_project))
    findings += naming_findings(parse_workflow(main, valid_project))
    assert {finding.code for finding in findings} == {
        "ST-NMG-008",
        "ST-NMG-016",
    }
