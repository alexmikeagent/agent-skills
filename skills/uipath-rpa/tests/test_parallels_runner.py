from pathlib import Path

from uipath_tooling.runners import parallels
from uipath_tooling.runners.parallels import ParallelsRunner, new_request


class Completed:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


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
