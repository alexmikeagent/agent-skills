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
        create_snapshot(request.project_path, snapshot)
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
        result_path = results / "validation-result.json"
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8-sig"))
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
        exit_code = (
            0
            if command.returncode == 0
            and all(
                result.get("gates", {}).get(name, {}).get("status")
                in {"passed", "not_run"}
                for name in ("compile", "execution")
            )
            else 1
        )
        if not request.keep_job and exit_code == 0:
            remove_snapshot(snapshot)
        return exit_code, result

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
