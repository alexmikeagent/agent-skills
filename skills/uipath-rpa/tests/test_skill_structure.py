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
        skill_root / "SKILL.md",
        skill_root / "references" / "code-mode-playbook.md",
        skill_root / "references" / "validation-contract.md",
        skill_root / "references" / "parallels-windows-bridge.md",
        skill_root / "references" / "reference-map.md",
        skill_root / "references" / "xaml" / "behavior-preserving-refactors.md",
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


def test_visual_guide_has_accessible_interaction_contract(skill_root: Path) -> None:
    source = (
        skill_root / "assets" / "visual-guides" / "uipath-tooling-improvement-plan.html"
    ).read_text()
    assert '<meta name="viewport"' in source
    assert 'role="tablist"' in source
    assert "prefers-reduced-motion" in source
    assert "@media print" in source
    assert '<title id="flow-title">' in source
