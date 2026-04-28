from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Bare project root containing an empty .shablon/templates/."""
    (tmp_path / ".shablon" / "templates").mkdir(parents=True)
    return tmp_path
