#!/usr/bin/env python3
"""Validate the personal Second Brain without third-party Python packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_VAULT = Path(
    "/Users/aman-mac-work/Documents/PERSONAL/Projects/obsidian-vaults/Second Brain"
)
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_SENSITIVITY = {"personal", "public", "sanitized"}
REQUIRED_DIRECTORIES = (
    "00 Inbox",
    "10 Projects",
    "20 Areas",
    "30 Knowledge",
    "40 Research",
    "50 Investigations",
    "60 Sources",
    "70 AI Sessions",
    "80 Archive",
    "90 Meta/Templates",
    "90 Meta/System",
    "Attachments",
)
TEXT_EXTENSIONS = {".md", ".mdx", ".html", ".json", ".canvas", ".base", ".css"}
SECRET_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("OpenAI-style key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "credential assignment",
        re.compile(
            r"(?i)\b(?:password|passwd|api[_-]?key|secret|access[_-]?token)\s*[:=]\s*['\"]?[^\s'\"]{8,}"
        ),
    ),
)


@dataclass
class Finding:
    level: str
    path: str
    message: str


def relative(path: Path, vault: Path) -> str:
    try:
        return str(path.relative_to(vault))
    except ValueError:
        return str(path)


def excluded(path: Path, vault: Path) -> bool:
    rel = relative(path, vault)
    return (
        rel.startswith("90 Meta/Skills Mirror/")
        or rel == "90 Meta/Skills Mirror"
        or "/node_modules/" in f"/{rel}/"
        or rel.startswith(".git/")
    )


def plugin_binary(path: Path, vault: Path) -> bool:
    rel = relative(path, vault)
    return rel.startswith(".obsidian/plugins/") and path.name in {
        "main.js",
        "styles.css",
        "manifest.json",
    }


def frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip("'\"")
    return values


def strip_fenced_code(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def validate_canvas(path: Path, data: object, vault: Path, findings: list[Finding]) -> None:
    if not isinstance(data, dict):
        findings.append(Finding("error", relative(path, vault), "Canvas root must be an object"))
        return
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        findings.append(Finding("error", relative(path, vault), "Canvas nodes and edges must be arrays"))
        return
    ids: list[str] = []
    node_ids: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            findings.append(Finding("error", relative(path, vault), "Canvas node is missing a string id"))
            continue
        ids.append(node["id"])
        node_ids.add(node["id"])
    for edge in edges:
        if not isinstance(edge, dict) or not isinstance(edge.get("id"), str):
            findings.append(Finding("error", relative(path, vault), "Canvas edge is missing a string id"))
            continue
        ids.append(edge["id"])
        if edge.get("fromNode") not in node_ids or edge.get("toNode") not in node_ids:
            findings.append(Finding("error", relative(path, vault), f"Canvas edge {edge['id']} has a dangling node reference"))
    if len(ids) != len(set(ids)):
        findings.append(Finding("error", relative(path, vault), "Canvas node and edge ids must be unique"))


def validate_mdx(path: Path, text: str, vault: Path, findings: list[Finding]) -> None:
    body = strip_fenced_code(text)
    checks = (
        (r"(?m)^\s*(?:import|export)\s", "imports and exports are forbidden"),
        (r"[{}]", "JavaScript expressions are forbidden"),
        (r"(?i)<\s*(?:script|iframe|object|embed)\b", "executable or embedded elements are forbidden"),
        (r"(?i)\bon[A-Za-z]+\s*=", "event-handler attributes are forbidden"),
        (r"(?i)dangerouslySetInnerHTML", "dangerouslySetInnerHTML is forbidden"),
        (r"(?i)(?:src\s*=\s*['\"]https?://|url\(\s*['\"]?https?://)", "remote runtime assets are forbidden"),
    )
    for pattern, message in checks:
        if re.search(pattern, body):
            findings.append(Finding("error", relative(path, vault), message))


def validate_html(path: Path, text: str, vault: Path, findings: list[Finding]) -> None:
    checks = (
        (r"(?i)<script\b[^>]*\bsrc\s*=", "external scripts are forbidden"),
        (r"(?i)<link\b[^>]*rel\s*=\s*['\"]stylesheet['\"][^>]*href\s*=\s*['\"]https?://", "external stylesheets are forbidden"),
        (r"(?i)(?:<img\b[^>]*src\s*=\s*['\"]https?://|url\(\s*['\"]?https?://)", "remote visual assets are forbidden"),
    )
    for pattern, message in checks:
        if re.search(pattern, text):
            findings.append(Finding("error", relative(path, vault), message))


def scan(vault: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not vault.is_dir():
        return [Finding("error", str(vault), "Vault path does not exist")]

    for directory in REQUIRED_DIRECTORIES:
        if not (vault / directory).is_dir():
            findings.append(Finding("error", directory, "Required directory is missing"))

    legacy_skills = Path("/Users/aman-mac-work/.codex/skills")
    if legacy_skills.exists():
        for entry in legacy_skills.iterdir():
            if entry.name != ".system":
                findings.append(
                    Finding(
                        "error",
                        str(entry),
                        "User skill entry must live under ~/.agents/skills",
                    )
                )
        system_skills = legacy_skills / ".system"
        marker = system_skills / ".codex-system-skills.marker"
        if system_skills.exists() and not marker.is_file():
            findings.append(
                Finding(
                    "error",
                    str(system_skills),
                    "Unrecognized .codex skill tree without the Codex system marker",
                )
            )

    for path in vault.rglob("*"):
        if path.is_dir() or excluded(path, vault):
            continue
        rel = relative(path, vault)
        try:
            size = path.stat().st_size
        except OSError as exc:
            findings.append(Finding("error", rel, f"Cannot stat file: {exc}"))
            continue
        if size > MAX_FILE_SIZE:
            findings.append(Finding("error", rel, f"File exceeds 20 MB ({size} bytes)"))
        if path.name.endswith(".icloud"):
            findings.append(Finding("error", rel, "iCloud placeholder is not downloaded"))
        if path.suffix.lower() not in TEXT_EXTENSIONS or plugin_binary(path, vault):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            findings.append(Finding("error", rel, f"Cannot read UTF-8 text: {exc}"))
            continue

        if path.suffix.lower() == ".md":
            metadata = frontmatter(text)
            if metadata is None:
                findings.append(Finding("error", rel, "Markdown note is missing valid frontmatter"))
            else:
                sensitivity = metadata.get("sensitivity")
                if sensitivity not in ALLOWED_SENSITIVITY:
                    findings.append(Finding("error", rel, f"Invalid or missing sensitivity: {sensitivity!r}"))

        if not rel.startswith(".obsidian/plugins/"):
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    findings.append(Finding("error", rel, f"Likely {label} detected"))

        if path.suffix.lower() in {".json", ".canvas"}:
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                findings.append(Finding("error", rel, f"Invalid JSON: {exc}"))
            else:
                if path.suffix.lower() == ".canvas":
                    validate_canvas(path, data, vault, findings)
        elif path.suffix.lower() == ".mdx":
            validate_mdx(path, text, vault, findings)
        elif path.suffix.lower() == ".html":
            validate_html(path, text, vault, findings)

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    findings = scan(args.vault.resolve())
    errors = [item for item in findings if item.level == "error"]
    if args.json:
        print(json.dumps({"ok": not errors, "findings": [asdict(item) for item in findings]}, indent=2))
    elif findings:
        for item in findings:
            print(f"[{item.level.upper()}] {item.path}: {item.message}")
        print(f"{len(errors)} error(s), {len(findings) - len(errors)} warning(s)")
    else:
        print(f"[OK] Vault health passed: {args.vault.resolve()}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
