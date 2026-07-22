#!/usr/bin/env python3
"""Collocated UiPath project inspection and validation CLI."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from uipath_tooling.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
