"""Tests for the rendering layer.

# spec: templates requirement=template-root
# spec: templates requirement=output-path-mirrors-template-path
# spec: templates requirement=parent-directories-are-created
# spec: templates requirement=trailing-newline-preserved
# spec: templates requirement=output-overwrites-existing-file
# spec: templates requirement=render-context-from-variables
# spec: templates requirement=output-mode-bits-mirror-template
"""

from __future__ import annotations

import stat
from pathlib import Path, PurePosixPath

from shablon.render import build_env, render_to_file
from tests.helpers import write


def _setup(project: Path) -> Path:
    return project / ".shablon" / "templates"


# spec: templates requirement=template-root scenario=include-from-sibling-partial
def test_include_resolves_via_template_root(project: Path) -> None:
    root = _setup(project)
    write(root / "_includes/header.md", "HEADER\n")
    write(root / "skills/foo/SKILL.md", '{% include "_includes/header.md" %}body\n')

    env = build_env(root)
    out = project / "skills/foo/SKILL.md"
    src = root / "skills/foo/SKILL.md"
    render_to_file(env, PurePosixPath("skills/foo/SKILL.md"), out, {}, src)

    assert out.read_text() == "HEADER\nbody\n"


# spec: templates requirement=trailing-newline-preserved scenario=template-ending-with-newline
def test_keep_trailing_newline(project: Path) -> None:
    root = _setup(project)
    write(root / "x.md", "hello\n")

    env = build_env(root)
    out = project / "x.md"
    render_to_file(env, PurePosixPath("x.md"), out, {}, root / "x.md")

    assert out.read_text() == "hello\n"


# spec: templates requirement=parent-directories-are-created scenario=first-render-into-a-fresh-project
def test_parent_dirs_created(project: Path) -> None:
    root = _setup(project)
    write(root / "plugins/claude/hooks/prime.md", "go")

    env = build_env(root)
    out = project / "plugins/claude/hooks/prime.md"
    render_to_file(
        env,
        PurePosixPath("plugins/claude/hooks/prime.md"),
        out,
        {},
        root / "plugins/claude/hooks/prime.md",
    )

    assert out.exists()
    assert out.parent == project / "plugins/claude/hooks"


# spec: templates requirement=output-overwrites-existing-file scenario=re-running-generate
def test_overwrites_existing_output(project: Path) -> None:
    root = _setup(project)
    write(root / "x.md", "second")
    out = project / "x.md"
    out.write_text("first", encoding="utf-8")

    env = build_env(root)
    render_to_file(env, PurePosixPath("x.md"), out, {}, root / "x.md")

    assert out.read_text() == "second"


# spec: templates requirement=render-context-from-variables scenario=top-level-keys-become-jinja-variables
def test_context_top_level_keys(project: Path) -> None:
    root = _setup(project)
    write(root / "x.md", "{{ version }}-{{ name }}")

    env = build_env(root)
    out = project / "x.md"
    render_to_file(
        env,
        PurePosixPath("x.md"),
        out,
        {"version": "1.2.0", "name": "foo"},
        root / "x.md",
    )

    assert out.read_text() == "1.2.0-foo"


def test_missing_variable_renders_empty(project: Path) -> None:
    """Default Jinja Undefined renders as empty; user validates output."""
    root = _setup(project)
    write(root / "x.md", "[{{ missing }}]")

    env = build_env(root)
    out = project / "x.md"
    render_to_file(env, PurePosixPath("x.md"), out, {}, root / "x.md")

    assert out.read_text() == "[]"


# spec: templates requirement=output-mode-bits-mirror-template scenario=executable-hook-script
def test_executable_template_produces_executable_output(project: Path) -> None:
    root = _setup(project)
    src = write(root / "hooks/post-tool.sh", "#!/bin/sh\necho hi\n")
    src.chmod(0o755)

    env = build_env(root)
    out = project / "hooks/post-tool.sh"
    render_to_file(env, PurePosixPath("hooks/post-tool.sh"), out, {}, src)

    assert (out.stat().st_mode & 0o777) == 0o755


# spec: templates requirement=output-mode-bits-mirror-template scenario=plain-markdown
def test_plain_template_keeps_default_mode(project: Path) -> None:
    root = _setup(project)
    src = write(root / "skills/foo/SKILL.md", "x")
    src.chmod(0o644)

    env = build_env(root)
    out = project / "skills/foo/SKILL.md"
    render_to_file(env, PurePosixPath("skills/foo/SKILL.md"), out, {}, src)

    assert (out.stat().st_mode & 0o777) == 0o644
