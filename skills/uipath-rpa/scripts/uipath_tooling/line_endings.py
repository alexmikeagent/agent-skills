from __future__ import annotations

import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from .project_model import Finding


def detect_bytes(data: bytes) -> str:
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n")
    bare_lf = lf - crlf
    if crlf and bare_lf:
        return "mixed"
    if crlf:
        return "crlf"
    if bare_lf:
        return "lf"
    return "none"


def detect(path: Path) -> str:
    return detect_bytes(path.read_bytes())


def expected_style(project_root: Path, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(project_root.resolve()).as_posix()
        completed = subprocess.run(
            ["git", "-C", str(project_root), "show", f"HEAD:{relative}"],
            check=False,
            capture_output=True,
        )
        if completed.returncode == 0:
            style = detect_bytes(completed.stdout)
            if style in {"crlf", "lf"}:
                return style
    except (OSError, ValueError):
        pass
    siblings = [detect(item) for item in path.parent.glob("*.xaml") if item != path]
    common = Counter(style for style in siblings if style in {"crlf", "lf"})
    return common.most_common(1)[0][0] if common else "crlf"


def check(project_root: Path, paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in paths:
        actual = detect(path)
        expected = expected_style(project_root, path)
        relative = path.relative_to(project_root).as_posix()
        if actual == "mixed":
            findings.append(
                Finding("EOL001", "error", "XAML contains mixed line endings", relative)
            )
        elif actual not in {expected, "none"}:
            findings.append(
                Finding(
                    "EOL002",
                    "warning",
                    f"XAML uses {actual.upper()}; expected {expected.upper()}",
                    relative,
                )
            )
        if path.read_bytes() and not path.read_bytes().endswith(b"\n"):
            findings.append(
                Finding("EOL003", "warning", "XAML has no final newline", relative)
            )
    return findings


def normalize(
    project_root: Path, paths: list[Path], write: bool
) -> list[dict[str, str]]:
    changes: list[dict[str, str]] = []
    for path in paths:
        data = path.read_bytes()
        actual = detect_bytes(data)
        expected = expected_style(project_root, path)
        normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if expected == "crlf":
            normalized = normalized.replace(b"\n", b"\r\n")
        if normalized and not normalized.endswith(
            b"\r\n" if expected == "crlf" else b"\n"
        ):
            normalized += b"\r\n" if expected == "crlf" else b"\n"
        if normalized != data:
            changes.append(
                {
                    "file": path.relative_to(project_root).as_posix(),
                    "from": actual,
                    "to": expected,
                }
            )
            if write:
                path.write_bytes(normalized)
                ET.fromstring(path.read_text(encoding="utf-8-sig"))
    return changes
