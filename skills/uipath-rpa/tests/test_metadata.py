import json
from pathlib import Path

from uipath_tooling.metadata import validate_metadata


def test_registered_test_is_recognized(valid_project: Path) -> None:
    project = json.loads((valid_project / "project.json").read_text())
    assert validate_metadata(valid_project, project) == []


def test_missing_registered_test_is_error(valid_project: Path) -> None:
    project = json.loads((valid_project / "project.json").read_text())
    project["designOptions"]["fileInfoCollection"][0]["fileName"] = (
        "Tests\\Missing.xaml"
    )
    findings = validate_metadata(valid_project, project)
    assert {finding.code for finding in findings} == {"META001", "META003"}


def test_registration_gate_promotes_unregistered_test_to_error(
    valid_project: Path,
) -> None:
    project = json.loads((valid_project / "project.json").read_text())
    project["designOptions"]["fileInfoCollection"] = []
    findings = validate_metadata(valid_project, project, require_registered_tests=True)
    registration = next(finding for finding in findings if finding.code == "META003")
    assert registration.severity == "error"
