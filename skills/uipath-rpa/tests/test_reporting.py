import json
from pathlib import Path

from uipath_tooling.project_model import Finding
from uipath_tooling.reporting import text_report, validation_result


def test_result_keeps_validation_gates_separate() -> None:
    result = validation_result(
        {
            "name": "Fixture",
            "targetFramework": "Windows",
            "expressionLanguage": "VisualBasic",
        },
        [Finding("X", "warning", "example")],
        ["Main.xaml"],
        "2026-01-01T00:00:00Z",
    )
    assert result["gates"]["static"]["status"] == "passed"
    assert result["gates"]["compile"]["status"] == "not_run"
    assert result["gates"]["execution"]["status"] == "not_run"
    assert "L2 compile: not_run" in text_report(result)


def test_versioned_schemas_are_valid_json(skill_root: Path) -> None:
    for path in (skill_root / "assets" / "schemas").glob("*.json"):
        assert json.loads(path.read_text())["$schema"].startswith(
            "https://json-schema.org/"
        )
