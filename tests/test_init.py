"""Tests for the init scaffolding module and CLI subcommand.

# spec: cli requirement=init-subcommand
# spec: cli requirement=init-refuses-existing-shablon
# spec: cli requirement=starter-config-toml
# spec: cli requirement=starter-vars-sh
# spec: cli requirement=starter-templates-tree
"""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

from shablon import init
from shablon.cli import main
from shablon.errors import ShablonError


# spec: cli requirement=init-subcommand scenario=default-invocation
def test_init_creates_skeleton(tmp_path: Path) -> None:
    init.run(tmp_path)

    shablon_dir = tmp_path / ".shablon"
    assert shablon_dir.is_dir()
    assert (shablon_dir / "config.toml").is_file()
    vars_path = shablon_dir / "vars.sh"
    assert vars_path.is_file()
    assert os.access(vars_path, os.X_OK)
    assert (shablon_dir / "templates").is_dir()
    assert (shablon_dir / "templates" / "_includes").is_dir()


# spec: cli requirement=init-subcommand scenario=default-invocation
def test_init_via_cli_returns_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    rc = main(["init"])
    assert rc == 0
    assert (tmp_path / ".shablon" / "config.toml").is_file()


# spec: cli requirement=init-subcommand scenario=help-output
def test_help_lists_init(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "init" in out
    assert "generate" in out


# spec: cli requirement=init-refuses-existing-shablon scenario=existing-shablon-directory
def test_init_refuses_existing_directory(tmp_path: Path) -> None:
    shablon_dir = tmp_path / ".shablon"
    shablon_dir.mkdir()
    sentinel = shablon_dir / "keep-me"
    sentinel.write_text("preserved")

    with pytest.raises(ShablonError) as exc:
        init.run(tmp_path)

    assert str(shablon_dir) in str(exc.value)
    assert sentinel.read_text() == "preserved"


# spec: cli requirement=init-refuses-existing-shablon scenario=existing-shablon-directory
def test_init_refuses_existing_directory_via_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / ".shablon").mkdir()
    monkeypatch.chdir(tmp_path)
    rc = main(["init"])
    assert rc == 1
    err = capsys.readouterr().err
    assert ".shablon" in err
    assert "already exists" in err


# spec: cli requirement=init-refuses-existing-shablon scenario=shablon-exists-as-a-file
def test_init_refuses_existing_file(tmp_path: Path) -> None:
    plain_file = tmp_path / ".shablon"
    plain_file.write_text("not a directory")

    with pytest.raises(ShablonError):
        init.run(tmp_path)

    assert plain_file.read_text() == "not a directory"


# spec: cli requirement=init-refuses-existing-shablon scenario=existing-shablon-directory
def test_init_refuses_existing_symlink(tmp_path: Path) -> None:
    target_dir = tmp_path / "other"
    target_dir.mkdir()
    link = tmp_path / ".shablon"
    link.symlink_to(target_dir)

    with pytest.raises(ShablonError):
        init.run(tmp_path)

    assert link.is_symlink()


# spec: cli requirement=starter-config-toml scenario=generated-config-is-valid-and-uses-defaults
# spec: cli requirement=starter-vars-sh scenario=generated-vars-sh-runs-cleanly
def test_init_then_generate_works(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init.run(tmp_path)

    template = tmp_path / ".shablon" / "templates" / "hello.txt"
    template.write_text("hello")

    monkeypatch.chdir(tmp_path)
    rc = main(["generate"])
    assert rc == 0
    assert (tmp_path / "hello.txt").read_text() == "hello"


# spec: cli requirement=starter-vars-sh scenario=generated-vars-sh-is-executable
def test_starter_vars_is_executable_and_prints_empty_object(tmp_path: Path) -> None:
    init.run(tmp_path)
    vars_path = tmp_path / ".shablon" / "vars.sh"
    mode = vars_path.stat().st_mode
    assert mode & stat.S_IXUSR
    result = subprocess.run([str(vars_path)], capture_output=True, check=True)
    assert result.stdout.strip() == b"{}"


# spec: cli requirement=starter-templates-tree scenario=empty-templates-tree
def test_starter_templates_tree_is_empty(tmp_path: Path) -> None:
    init.run(tmp_path)
    templates = tmp_path / ".shablon" / "templates"
    entries = list(templates.iterdir())
    assert entries == [templates / "_includes"]
    assert list((templates / "_includes").iterdir()) == []
