from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from ..job_snapshot import create_snapshot, remove_snapshot
from ..project_model import gate, now_iso
from .base import ValidationRequest


GATE_STATUSES = {"passed", "failed", "blocked", "not_run"}


def result_contract_error(result: object, request: ValidationRequest) -> str | None:
    if not isinstance(result, dict):
        return "validation result is not an object"
    if result.get("schema") != "uipath-validation-result/v1":
        return "validation result schema is invalid"
    if result.get("job_id") != request.job_id:
        return "validation result job_id does not match the request"
    for key in (
        "project",
        "environment",
        "gates",
        "findings",
        "tests",
        "artifacts",
        "started_at",
        "finished_at",
    ):
        if key not in result:
            return f"validation result is missing {key}"
    gates = result.get("gates")
    if not isinstance(gates, dict):
        return "validation result gates is not an object"
    for name in ("static", "compile", "execution", "uat"):
        gate_value = gates.get(name)
        if (
            not isinstance(gate_value, dict)
            or gate_value.get("status") not in GATE_STATUSES
        ):
            return f"validation result gate is invalid: {name}"
    for key in ("findings", "tests", "artifacts"):
        if not isinstance(result.get(key), list):
            return f"validation result {key} is not an array"
    return None


def requested_mode_passed(result: dict[str, Any], request: ValidationRequest) -> bool:
    gates = result["gates"]
    if gates["compile"]["status"] != "passed":
        return False
    if request.mode == "build":
        return gates["execution"]["status"] == "not_run"
    if gates["execution"]["status"] != "passed":
        return False
    if request.mode == "build-and-test":
        tests = result.get("tests", [])
        return bool(tests) and all(item.get("status") == "passed" for item in tests)
    return request.mode == "run-workflow"


def _run(arguments: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments, check=False, capture_output=True, text=True, timeout=timeout
    )


class ParallelsRunner:
    def __init__(self, vm_name: str, skill_root: Path, jobs_root: Path | None = None):
        self.vm_name = vm_name
        self.skill_root = skill_root
        self.jobs_root = jobs_root or Path.home() / ".codex" / "uipath-rpa" / "jobs"

    def _guest(
        self, *arguments: str, timeout: int = 60
    ) -> subprocess.CompletedProcess[str]:
        return _run(
            ["prlctl", "exec", self.vm_name, "--current-user", *arguments],
            timeout=timeout,
        )

    def preflight(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        prlctl = shutil.which("prlctl")
        checks.append(
            {
                "name": "prlctl",
                "status": "passed" if prlctl else "blocked",
                "detail": prlctl,
            }
        )
        if not prlctl:
            return self._preflight_result(checks)
        listing = _run([prlctl, "list", "--all"])
        running = (
            listing.returncode == 0
            and self.vm_name in listing.stdout
            and "running" in listing.stdout.lower()
        )
        checks.append(
            {
                "name": "vm_running",
                "status": "passed" if running else "blocked",
                "detail": self.vm_name,
            }
        )
        if not running:
            return self._preflight_result(checks)
        version = self._guest("cmd.exe", "/d", "/c", "ver")
        checks.append(
            {
                "name": "guest_exec",
                "status": "passed" if version.returncode == 0 else "blocked",
                "detail": version.stdout.strip() or version.stderr.strip(),
            }
        )
        shared = self._guest(
            "cmd.exe", "/d", "/c", "if exist \\\\Mac\\Home (exit /b 0) else (exit /b 1)"
        )
        checks.append(
            {
                "name": "mac_home_share",
                "status": "passed" if shared.returncode == 0 else "blocked",
                "detail": "\\\\Mac\\Home",
            }
        )
        architecture = self._guest(
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()",
        )
        architecture_name = architecture.stdout.strip().lower()
        architecture_supported = architecture.returncode == 0 and architecture_name in {
            "x64",
            "amd64",
        }
        checks.append(
            {
                "name": "studio_supported_architecture",
                "status": "passed" if architecture_supported else "blocked",
                "detail": architecture.stdout.strip()
                or architecture.stderr.strip()
                or "unknown",
                "remediation": None
                if architecture_supported
                else "Use an x64 Windows runner; UiPath Studio does not support Windows ARM.",
            }
        )
        tools = self._guest(
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$uip=(Get-Command uip -ErrorAction SilentlyContinue); $studio=(Get-Command UiPath.Studio.exe -ErrorAction SilentlyContinue); if(-not $studio){$studio=Get-ChildItem \"$env:LOCALAPPDATA\\Programs\\UiPath\",\"C:\\Program Files\\UiPath\" -Filter UiPath.Studio.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1}; if($uip){'UIP='+$uip.Source}; if($studio){'STUDIO='+$studio.FullName}; if($uip -and $studio){exit 0}else{exit 3}",
        )
        checks.append(
            {
                "name": "uipath_toolchain",
                "status": "passed" if tools.returncode == 0 else "blocked",
                "detail": tools.stdout.strip() or "UiPath CLI or Studio not found",
            }
        )
        return self._preflight_result(checks)

    def _preflight_result(self, checks: list[dict[str, Any]]) -> dict[str, Any]:
        status = (
            "passed"
            if checks and all(item["status"] == "passed" for item in checks)
            else "blocked"
        )
        return {
            "schema": "uipath-runner-preflight/v1",
            "runner": "parallels",
            "vm_name": self.vm_name,
            "status": status,
            "checks": checks,
        }

    def validate(self, request: ValidationRequest) -> tuple[int, dict[str, Any]]:
        started = now_iso()
        self._validate_test_paths(request)
        if request.mode == "run-workflow" and not request.allow_side_effects:
            return 4, self._blocked_result(
                request,
                started,
                "Production workflow execution requires --allow-side-effects",
            )
        preflight = self.preflight()
        if preflight["status"] != "passed":
            return 3, self._blocked_result(
                request, started, "Parallels UiPath preflight is blocked", preflight
            )

        host_job = self.jobs_root / request.job_id
        snapshot = host_job / "project"
        results = host_job / "results"
        host_job.mkdir(parents=True, exist_ok=False)
        try:
            create_snapshot(request.project_path, snapshot)
        except Exception:
            shutil.rmtree(host_job)
            raise
        results.mkdir()
        request_path = host_job / "validation-request.json"
        request_value = {
            "schema": "uipath-validation-request/v1",
            "job_id": request.job_id,
            "project_path": "project",
            "mode": request.mode,
            "tests": {
                "selection": request.test_selection,
                "paths": list(request.test_paths),
            },
            "allow_side_effects": request.allow_side_effects,
            "keep_job": request.keep_job,
        }
        request_path.write_text(
            json.dumps(request_value, indent=2) + "\n", encoding="utf-8"
        )

        relative_job = (
            host_job.resolve()
            .relative_to(Path.home().resolve())
            .as_posix()
            .replace("/", "\\")
        )
        windows_job = f"\\\\Mac\\Home\\{relative_job}"
        runner_script = (
            self.skill_root / "scripts" / "windows" / "Invoke-UiPathValidation.ps1"
        )
        relative_script = (
            runner_script.resolve()
            .relative_to(Path.home().resolve())
            .as_posix()
            .replace("/", "\\")
        )
        windows_script = f"\\\\Mac\\Home\\{relative_script}"
        try:
            command = self._guest(
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                windows_script,
                "-RequestPath",
                f"{windows_job}\\validation-request.json",
                "-HostJobPath",
                windows_job,
                timeout=3600,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            result = self._blocked_result(
                request, started, f"Windows runner transport failed: {error}"
            )
            result["findings"][0]["code"] = "RUN004"
            result_path = results / "validation-result.json"
            result_path.write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            if not request.keep_job:
                remove_snapshot(snapshot)
            return 2, result
        result_path = results / "validation-result.json"
        contract_error: str | None = None
        if result_path.exists():
            try:
                result = json.loads(result_path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as error:
                result = self._blocked_result(
                    request,
                    started,
                    f"Windows runner produced an invalid validation result: {error}",
                )
                result["findings"][0]["code"] = "RUN003"
                contract_error = str(error)
            else:
                contract_error = result_contract_error(result, request)
                if contract_error:
                    result = self._blocked_result(
                        request,
                        started,
                        f"Windows runner result contract failed: {contract_error}",
                    )
                    result["findings"][0]["code"] = "RUN003"
        else:
            result = self._blocked_result(
                request,
                started,
                "Windows runner did not produce validation-result.json",
            )
            result["findings"].append(
                {
                    "code": "RUN002",
                    "severity": "error",
                    "message": command.stderr.strip() or command.stdout.strip(),
                }
            )
            result_path.write_text(
                json.dumps(result, indent=2) + "\n", encoding="utf-8"
            )
            contract_error = "validation-result.json is missing"
        if contract_error:
            exit_code = 2
        elif command.returncode in {2, 3, 4}:
            exit_code = command.returncode
        elif command.returncode != 0:
            exit_code = 1
        else:
            exit_code = 0 if requested_mode_passed(result, request) else 1
        if not request.keep_job:
            remove_snapshot(snapshot)
        return exit_code, result

    @staticmethod
    def _validate_test_paths(request: ValidationRequest) -> None:
        project_root = request.project_path.resolve()
        for value in request.test_paths:
            candidate = Path(value)
            if candidate.is_absolute() or candidate.suffix.lower() != ".xaml":
                raise ValueError(f"Test path must be a relative XAML path: {value}")
            try:
                (project_root / candidate).resolve().relative_to(project_root)
            except ValueError as error:
                raise ValueError(
                    f"Test path escapes the project root: {value}"
                ) from error

    def _blocked_result(
        self,
        request: ValidationRequest,
        started: str,
        message: str,
        preflight: dict | None = None,
    ) -> dict[str, Any]:
        finding: dict[str, Any] = {
            "code": "RUN001",
            "severity": "error",
            "message": message,
            "gate": "compile",
        }
        if preflight:
            finding["evidence"] = preflight
        return {
            "schema": "uipath-validation-result/v1",
            "job_id": request.job_id,
            "project": {"name": request.project_path.name},
            "environment": {
                "host_os": "macOS",
                "runner": "parallels",
                "vm_name": self.vm_name,
            },
            "gates": {
                "static": gate("not_run"),
                "compile": gate("blocked"),
                "execution": gate("not_run"),
                "uat": gate("not_run"),
            },
            "findings": [finding],
            "tests": [],
            "artifacts": [],
            "started_at": started,
            "finished_at": now_iso(),
        }


def new_request(
    project_path: Path,
    mode: str,
    tests: str,
    test_paths: list[str],
    allow_side_effects: bool,
    keep_job: bool,
) -> ValidationRequest:
    return ValidationRequest(
        str(uuid.uuid4()),
        project_path,
        mode,
        tests,
        tuple(test_paths),
        allow_side_effects,
        keep_job,
    )
