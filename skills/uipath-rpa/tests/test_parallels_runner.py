from pathlib import Path

import pytest

from uipath_tooling.runners import parallels
from uipath_tooling.runners.parallels import (
    ParallelsRunner,
    new_request,
    requested_mode_passed,
    result_contract_error,
)


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _result(job_id: str, compile_status: str, execution_status: str, tests=None):
    return {
        "schema": "uipath-validation-result/v1",
        "job_id": job_id,
        "project": {"name": "Fixture"},
        "environment": {"runner": "parallels"},
        "gates": {
            "static": {"status": "not_run"},
            "compile": {"status": compile_status},
            "execution": {"status": execution_status},
            "uat": {"status": "not_run"},
        },
        "findings": [],
        "tests": tests or [],
        "artifacts": [],
        "started_at": "2026-08-08T00:00:00Z",
        "finished_at": "2026-08-08T00:00:01Z",
    }


def test_preflight_reports_blocked_without_prlctl(
    monkeypatch, skill_root: Path
) -> None:
    monkeypatch.setattr(parallels.shutil, "which", lambda _: None)
    result = ParallelsRunner("Windows 11", skill_root).preflight()
    assert result["status"] == "blocked"
    assert result["checks"][0]["name"] == "prlctl"


def test_side_effecting_run_is_refused_before_preflight(
    valid_project: Path, skill_root: Path
) -> None:
    runner = ParallelsRunner("Windows 11", skill_root)
    request = new_request(valid_project, "run-workflow", "changed", [], False, False)
    code, result = runner.validate(request)
    assert code == 4
    assert result["gates"]["compile"]["status"] == "blocked"


def test_test_path_cannot_escape_project(
    valid_project: Path, skill_root: Path
) -> None:
    runner = ParallelsRunner("Windows 11", skill_root)
    request = new_request(
        valid_project, "build-and-test", "paths", ["../outside.xaml"], False, False
    )
    with pytest.raises(ValueError, match="escapes the project root"):
        runner.validate(request)


def test_build_and_test_requires_at_least_one_passed_test(
    valid_project: Path,
) -> None:
    request = new_request(
        valid_project, "build-and-test", "changed", [], False, False
    )
    empty = _result(request.job_id, "passed", "not_run")
    assert result_contract_error(empty, request) is None
    assert not requested_mode_passed(empty, request)

    passed = _result(
        request.job_id,
        "passed",
        "passed",
        [{"path": "Tests/TC_Child.xaml", "status": "passed"}],
    )
    assert requested_mode_passed(passed, request)


def test_result_contract_rejects_wrong_job_and_invalid_status(
    valid_project: Path,
) -> None:
    request = new_request(valid_project, "build", "changed", [], False, False)
    wrong_job = _result("different-job", "passed", "not_run")
    assert "job_id" in result_contract_error(wrong_job, request)

    invalid_gate = _result(request.job_id, "green", "not_run")
    assert "compile" in result_contract_error(invalid_gate, request)


def test_arm_guest_is_reported_as_unsupported(monkeypatch, skill_root: Path) -> None:
    monkeypatch.setattr(parallels.shutil, "which", lambda _: "/usr/local/bin/prlctl")
    monkeypatch.setattr(
        parallels, "_run", lambda *args, **kwargs: Completed(0, "Windows 11 running")
    )
    runner = ParallelsRunner("Windows 11", skill_root)
    responses = iter(
        [
            Completed(0, "Microsoft Windows"),
            Completed(0, ""),
            Completed(0, "Arm64"),
            Completed(3, ""),
        ]
    )
    monkeypatch.setattr(runner, "_guest", lambda *args, **kwargs: next(responses))
    result = runner.preflight()
    architecture = next(
        check
        for check in result["checks"]
        if check["name"] == "studio_supported_architecture"
    )
    assert architecture["status"] == "blocked"
    assert "x64 Windows runner" in architecture["remediation"]
