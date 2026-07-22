from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WorkflowArgument:
    name: str
    direction: str
    type_name: str


@dataclass(frozen=True)
class InvokeArgument:
    name: str
    direction: str
    type_name: str


@dataclass
class InvokeInfo:
    target: str
    display_name: str
    id_ref: str | None
    arguments: list[InvokeArgument] = field(default_factory=list)


@dataclass
class WorkflowInfo:
    path: Path
    relative_path: str
    root: Any
    source: str
    arguments: dict[str, WorkflowArgument]
    invokes: list[InvokeInfo]
    id_refs: list[str]
    activity_names: list[str]
    activity_count: int
    variable_count: int
    max_depth: int


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    message: str
    file: str | None = None
    line: int | None = None
    activity_id: str | None = None
    evidence: str | None = None
    remediation: str | None = None
    gate: str = "static"

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def gate(status: str, summary: str | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"status": status}
    if summary:
        result["summary"] = summary
    return result
