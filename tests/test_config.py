"""Tests for .shablon/config.toml loading and validation.

# spec: config requirement=optional-config-file
# spec: config requirement=config-schema
# spec: config requirement=strict-validation
# spec: config requirement=parse-errors-halt-early
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shablon.config import Config, load
from shablon.errors import ShablonError


# spec: config requirement=optional-config-file scenario=no-config-file
def test_missing_config_returns_defaults(project: Path) -> None:
    cfg = load(project / ".shablon")
    assert cfg == Config(include=[], partials_dir="_includes")


# spec: config requirement=optional-config-file scenario=empty-config-file
def test_empty_config_returns_defaults(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text("", encoding="utf-8")
    cfg = load(project / ".shablon")
    assert cfg == Config(include=[], partials_dir="_includes")


# spec: config requirement=config-schema
def test_valid_include_and_partials_dir(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        'include = [".gitignore", ".env*"]\npartials_dir = "_partials"\n',
        encoding="utf-8",
    )
    cfg = load(project / ".shablon")
    assert cfg.include == [".gitignore", ".env*"]
    assert cfg.partials_dir == "_partials"


# spec: config requirement=strict-validation scenario=unknown-key
def test_unknown_key_rejected(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        'inculde = [".env"]\n', encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="inculde"):
        load(project / ".shablon")


# spec: config requirement=strict-validation scenario=wrong-type-for-include
def test_include_must_be_array(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        'include = ".env"\n', encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="include"):
        load(project / ".shablon")


def test_include_array_of_strings_only(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        "include = [1, 2]\n", encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="include"):
        load(project / ".shablon")


# spec: config requirement=strict-validation scenario=partials-dir-with-path-separator
def test_partials_dir_rejects_separator(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        'partials_dir = "shared/_partials"\n', encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="partials_dir"):
        load(project / ".shablon")


@pytest.mark.parametrize("bad", ["", ".", ".."])
def test_partials_dir_rejects_dot_and_empty(project: Path, bad: str) -> None:
    (project / ".shablon" / "config.toml").write_text(
        f'partials_dir = "{bad}"\n', encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="partials_dir"):
        load(project / ".shablon")


def test_partials_dir_must_be_string(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        "partials_dir = 5\n", encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="partials_dir"):
        load(project / ".shablon")


# spec: config requirement=parse-errors-halt-early scenario=malformed-toml
def test_malformed_toml_raises(project: Path) -> None:
    (project / ".shablon" / "config.toml").write_text(
        "include = [\n", encoding="utf-8"
    )
    with pytest.raises(ShablonError, match="config.toml"):
        load(project / ".shablon")
