"""End-to-end integration test modelled on tiquette's plugin_src layout.

Runs the installed `shablon` binary as a subprocess against a temp project
shaped like tiquette/plugin_src/templates/. Validates the full pipeline:
upward discovery, vars execution, partials, dotfile re-inclusion, mode-bit
mirroring, output paths.

# spec: cli requirement=generate-subcommand
# spec: cli requirement=project-root-discovery
# spec: templates requirement=template-root
# spec: templates requirement=output-path-mirrors-template-path
# spec: templates requirement=output-mode-bits-mirror-template
# spec: templates requirement=dotfiles-skipped-by-default
# spec: templates requirement=partials-directories-are-partials-only
# spec: variables requirement=top-level-keys-become-render-variables
# spec: config requirement=config-schema
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tests.helpers import make_executable, write

SHABLON = shutil.which("shablon")


@pytest.fixture
def tiquette_like(tmp_path: Path) -> Path:
    """A project tree mirroring tiquette/plugin_src/templates/."""
    root = tmp_path / "demo-project"
    shab = root / ".shablon"
    tpl = shab / "templates"

    # Partials: rendered into other templates, never written to output.
    write(
        tpl / "_includes/prime.md",
        textwrap.dedent(
            """\
            This project uses `tq` for task tracking. Tickets live in `.tickets/`.

            Use `Bash(tq ...)` for work tracking instead of Todo*.
            """
        ),
    )
    write(
        tpl / "_includes/meta.yaml",
        textwrap.dedent(
            """\
            metadata:
              author: plugin_src
              version: {{ version }}
              note: Generated. Do not modify
            """
        ),
    )

    # Real outputs.
    write(
        tpl / "plugins/claude/hooks/prime.md",
        textwrap.dedent(
            """\
            <system-reminder>
            # claudeMd (continued)
            {% include "_includes/prime.md" -%}
            </system-reminder>
            """
        ),
    )

    hook = write(
        tpl / "plugins/claude/hooks/post-tool.sh",
        textwrap.dedent(
            """\
            #!/bin/sh
            echo "tiq-demo {{ version }}"
            """
        ),
    )
    make_executable(hook)

    write(
        tpl / "skills/tiq/SKILL.md",
        textwrap.dedent(
            """\
            ---
            name: tiq
            description: A demo skill rendered from a shablon template.
            {% include "_includes/meta.yaml" -%}
            ---

            # Tiq

            Help text from the project CLI:

            ```
            {{ help_text }}
            ```
            """
        ),
    )

    # Dotfile: skipped by default. Re-enabled via config.
    write(tpl / ".gitignore", "node_modules/\n*.pyc\n")
    write(tpl / "skills/tiq/.DS_Store", "binary noise that must NOT be rendered")

    # Config re-includes .gitignore but not .DS_Store.
    write(shab / "config.toml", 'include = [".gitignore"]\n')

    # vars.py emits the same shape tiquette uses: help_text + version.
    vars_py = write(
        shab / "vars.py",
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            print(json.dumps({
                "help_text": "Usage: tq <command> [args]",
                "version": "9.9.9",
            }))
            """
        ),
    )
    make_executable(vars_py)

    return root


@pytest.mark.skipif(SHABLON is None, reason="shablon not installed")
def test_tiquette_like_generation(tiquette_like: Path) -> None:
    # Run from a nested subdirectory to exercise upward project-root discovery.
    nested = tiquette_like / "src" / "deep"
    nested.mkdir(parents=True)

    result = subprocess.run(
        [SHABLON, "generate"],
        cwd=nested,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, (
        f"shablon failed (exit {result.returncode})\n"
        f"--- stdout ---\n{result.stdout}\n"
        f"--- stderr ---\n{result.stderr}"
    )

    # Every expected output exists; nothing from _includes leaks.
    expected_outputs = {
        "plugins/claude/hooks/prime.md",
        "plugins/claude/hooks/post-tool.sh",
        "skills/tiq/SKILL.md",
        ".gitignore",
    }
    for rel in expected_outputs:
        assert (tiquette_like / rel).is_file(), f"missing output: {rel}"

    # Partials must not have written to a top-level _includes/ in the project.
    assert not (tiquette_like / "_includes").exists(), (
        "_includes/ should never appear in the output tree"
    )

    # Default-skipped dotfile that wasn't re-included must not appear.
    assert not (tiquette_like / "skills/tiq/.DS_Store").exists(), (
        ".DS_Store was not in include patterns and must not be rendered"
    )

    # Stdout reports each rendered file in lexical order, partials excluded.
    written_lines = [
        line.removeprefix("wrote ")
        for line in result.stdout.strip().splitlines()
        if line.startswith("wrote ")
    ]
    assert written_lines == sorted(expected_outputs)

    # Variable substitution in templates and via partial.
    skill = (tiquette_like / "skills/tiq/SKILL.md").read_text()
    assert "version: 9.9.9" in skill, skill
    assert "Usage: tq <command> [args]" in skill, skill

    # Partial-include rendered into the hook prime.md.
    prime = (tiquette_like / "plugins/claude/hooks/prime.md").read_text()
    assert "tq" in prime
    assert "Tickets live in `.tickets/`" in prime

    # Rendered shell script substituted version and kept exec bit.
    hook = tiquette_like / "plugins/claude/hooks/post-tool.sh"
    assert "tiq-demo 9.9.9" in hook.read_text()
    assert os.access(hook, os.X_OK), "rendered hook lost its executable bit"

    # Re-included dotfile is rendered as-is.
    assert (tiquette_like / ".gitignore").read_text() == "node_modules/\n*.pyc\n"


@pytest.mark.skipif(SHABLON is None, reason="shablon not installed")
def test_rerun_overwrites_outputs(tiquette_like: Path) -> None:
    """Second `shablon generate` call updates outputs to reflect new vars."""
    subprocess.run([SHABLON, "generate"], cwd=tiquette_like, check=True)

    # Bump the version in vars.py and re-run.
    vars_py = tiquette_like / ".shablon" / "vars.py"
    vars_py.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            print(json.dumps({
                "help_text": "Usage: tq <command> [args]",
                "version": "10.0.0",
            }))
            """
        ),
        encoding="utf-8",
    )
    make_executable(vars_py)

    result = subprocess.run(
        [SHABLON, "generate"],
        cwd=tiquette_like,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0

    skill = (tiquette_like / "skills/tiq/SKILL.md").read_text()
    assert "version: 10.0.0" in skill
    assert "version: 9.9.9" not in skill
