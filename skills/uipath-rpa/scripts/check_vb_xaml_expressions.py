#!/usr/bin/env python3
"""Catch common UiPath VB-expression failures that XML validation misses."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from uipath_tooling.expressions import check_path as check  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    files = [
        child
        for path in args.paths
        for child in (sorted(path.rglob("*.xaml")) if path.is_dir() else [path])
    ]
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
