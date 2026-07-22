from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


@pytest.fixture
def skill_root() -> Path:
    return SKILL_ROOT


@pytest.fixture
def valid_project(tmp_path: Path) -> Path:
    source = SKILL_ROOT / "tests" / "fixtures" / "valid-project"
    destination = tmp_path / "ValidFixture"
    shutil.copytree(source, destination)
    return destination
