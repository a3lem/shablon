"""CLI-level tests via the public entry point.

# spec: cli requirement=generate-subcommand
# spec: cli requirement=missing-configuration-errors-cleanly
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shablon.cli import main
from tests.helpers import write


# spec: cli requirement=generate-subcommand scenario=help-output
def test_help_lists_generate(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    assert "generate" in capsys.readouterr().out


def test_generate_returns_zero(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write(project / ".shablon" / "templates" / "x.md", "hi")
    monkeypatch.chdir(project)
    rc = main(["generate"])
    assert rc == 0
    assert (project / "x.md").read_text() == "hi"


# spec: cli requirement=missing-configuration-errors-cleanly scenario=no-shablon-directory
def test_missing_shablon_returns_one(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    rc = main(["generate"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "no .shablon/" in err
