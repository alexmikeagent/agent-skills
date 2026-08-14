import json
import re
from pathlib import Path


def test_collocated_tooling_contract(skill_root: Path) -> None:
    required = [
        "SKILL.md",
        "agents/openai.yaml",
        "scripts/uipath_tool.py",
        "scripts/windows/Invoke-UiPathValidation.ps1",
        "assets/policies/baseline.json",
        "assets/schemas/validation-result-v1.schema.json",
    ]
    for relative in required:
        assert (skill_root / relative).is_file(), relative


def test_policy_json_files_parse(skill_root: Path) -> None:
    for path in (skill_root / "assets" / "policies").glob("*.json"):
        assert json.loads(path.read_text())["schema"] == "uipath-policy/v1"


def test_skill_relative_markdown_links_resolve(skill_root: Path) -> None:
    paths = [
        path
        for path in skill_root.rglob("*.md")
        if "legacy" not in path.parts and "activity-docs" not in path.parts
    ]
    missing = []
    for path in paths:
        for target in re.findall(
            r"\[[^]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")
        ):
            if target.startswith(("http://", "https://", "#", "{")):
                continue
            file_target = target.split("#", 1)[0]
            if file_target and not (path.parent / file_target).exists():
                missing.append(f"{path.relative_to(skill_root)} -> {target}")
    assert missing == []


def test_canonical_references_do_not_point_to_vanished_skill_rules(
    skill_root: Path,
) -> None:
    stale = re.compile(
        r"SKILL (?:Rule|§)|Common Rule|Critical Rules|Validation Iteration Loop|#validation-iteration-loop"
    )
    findings = []
    for path in (skill_root / "references").rglob("*.md"):
        if "legacy" in path.parts or "activity-docs" in path.parts:
            continue
        if stale.search(path.read_text(encoding="utf-8")):
            findings.append(path.relative_to(skill_root).as_posix())
    assert findings == []


def test_windows_runner_verifies_snapshot_manifest(skill_root: Path) -> None:
    source = (
        skill_root / "scripts" / "windows" / "Invoke-UiPathValidation.ps1"
    ).read_text(encoding="utf-8")
    for marker in (
        ".uipath-snapshot.json",
        "Get-FileHash",
        "WIN013",
        "WIN014",
        "WIN015",
    ):
        assert marker in source
