"""End-to-end tests for the generate orchestration.

# spec: cli requirement=generate-subcommand
# spec: cli requirement=missing-templates-directory-errors-cleanly
# spec: cli requirement=empty-templates-tree-is-a-no-op
# spec: cli requirement=errors-halt-generation
# spec: templates requirement=output-path-mirrors-template-path
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from shablon import generate
from shablon.errors import ShablonError
from tests.helpers import vars_script, write


# spec: cli requirement=generate-subcommand scenario=invoking-generate-from-a-configured-project
# spec: templates requirement=output-path-mirrors-template-path scenario=nested-template
# spec: templates requirement=output-path-mirrors-template-path scenario=top-level-template
def test_end_to_end(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = project / ".shablon" / "templates"
    write(root / "AGENTS.md", "# {{ name }}")
    write(root / "plugins/claude/hooks/prime.md", "version={{ version }}")
    vars_script(
        project / ".shablon",
        "py",
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            print(json.dumps({"name": "Demo", "version": "0.1"}))
            """
        ),
    )

    generate.run(start=project)

    assert (project / "AGENTS.md").read_text() == "# Demo"
    assert (project / "plugins/claude/hooks/prime.md").read_text() == "version=0.1"

    captured = capsys.readouterr()
    assert "wrote AGENTS.md" in captured.out
    assert "wrote plugins/claude/hooks/prime.md" in captured.out


# spec: cli requirement=missing-templates-directory-errors-cleanly scenario=empty-shablon-directory
def test_missing_templates_dir_errors(tmp_path: Path) -> None:
    (tmp_path / ".shablon").mkdir()
    with pytest.raises(ShablonError, match="templates"):
        generate.run(start=tmp_path)


# spec: cli requirement=empty-templates-tree-is-a-no-op scenario=templates-directory-contains-only-_includes
def test_only_includes_is_no_op(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(project / ".shablon" / "templates" / "_includes" / "foo.md", "x")
    generate.run(start=project)
    captured = capsys.readouterr()
    assert captured.out == ""


# spec: cli requirement=errors-halt-generation scenario=jinja-syntax-error-in-second-template
def test_first_writes_then_second_fails(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "a.md", "ok")
    write(root / "b.md", "{% if %}")  # malformed Jinja

    with pytest.raises(Exception):
        generate.run(start=project)

    assert (project / "a.md").read_text() == "ok"
    assert not (project / "b.md").exists()
