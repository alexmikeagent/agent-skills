from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ValidationRequest:
    job_id: str
    project_path: Path
    mode: str
    test_selection: str
    test_paths: tuple[str, ...]
    allow_side_effects: bool
    keep_job: bool


class Runner(Protocol):
    def preflight(self) -> dict[str, Any]: ...

    def validate(self, request: ValidationRequest) -> tuple[int, dict[str, Any]]: ...
