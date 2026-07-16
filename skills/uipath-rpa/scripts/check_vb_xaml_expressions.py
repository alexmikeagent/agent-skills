#!/usr/bin/env python3
"""Catch common UiPath VB-expression failures that XML validation misses."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLUENT_AFTER_NEWLINE = re.compile(
    r"\.\s*\r?\n\s*(?:Select|Where|Distinct|OrderBy|OrderByDescending|Take|ToList|ToArray)\s*\(",
    re.IGNORECASE,
)
UNQUALIFIED_REGEX = re.compile(r"(?<![\w.])Regex\.")


def expressions(root: ET.Element):
    for element in root.iter():
        for value in element.attrib.values():
            if value.startswith("[") and value.endswith("]"):
                yield value[1:-1]
        if element.text:
            value = element.text.strip()
            if value.startswith("[") and value.endswith("]"):
                yield value[1:-1]


def parenthesis_error(expression: str) -> str | None:
    depth = 0
    in_string = False
    index = 0
    while index < len(expression):
        character = expression[index]
        if character == '"':
            if in_string and index + 1 < len(expression) and expression[index + 1] == '"':
                index += 2
                continue
            in_string = not in_string
        elif not in_string and character == "(":
            depth += 1
        elif not in_string and character == ")":
            depth -= 1
            if depth < 0:
                return "closes a parenthesis before opening it"
        index += 1
    if in_string:
        return "contains an unterminated VB string literal"
    if depth:
        return f"has {depth} unclosed parenthesis(es)"
    return None


def check(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        return [f"XML parse failed: {error}"]

    source = path.read_text(encoding="utf-8-sig")
    imports_regex = "<x:String>System.Text.RegularExpressions</x:String>" in source
    failures: list[str] = []
    for number, expression in enumerate(expressions(root), start=1):
        error = parenthesis_error(expression)
        if error:
            failures.append(f"expression {number} {error}")
        if FLUENT_AFTER_NEWLINE.search(expression):
            failures.append(
                f"expression {number} uses a fluent member after a physical newline; "
                "keep the chain on one line or split it into Assign activities"
            )
        if UNQUALIFIED_REGEX.search(expression) and not imports_regex:
            failures.append(
                f"expression {number} uses unqualified Regex without the "
                "System.Text.RegularExpressions VB import"
            )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    files = [child for path in args.paths for child in (sorted(path.rglob("*.xaml")) if path.is_dir() else [path])]
    failed = False
    for path in files:
        failures = check(path)
        if failures:
            failed = True
            for failure in failures:
                print(f"{path}: {failure}")
    if not failed:
        print(f"VB/XAML expression checks passed for {len(files)} file(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
