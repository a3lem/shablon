"""Tests for project-root and template discovery.

# spec: cli requirement=project-root-discovery
# spec: templates requirement=partials-directories-are-partials-only
# spec: templates requirement=dotfiles-skipped-by-default
# spec: templates requirement=deterministic-render-order
# spec: templates requirement=symlinks-are-followed
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shablon.discovery import find_project_root, find_templates
from shablon.errors import ShablonError
from tests.helpers import write


# --- project root discovery ----------------------------------------------


# spec: cli requirement=project-root-discovery scenario=run-from-project-root
def test_find_project_root_from_root(project: Path) -> None:
    assert find_project_root(project) == project.resolve()


# spec: cli requirement=project-root-discovery scenario=run-from-nested-subdirectory
def test_find_project_root_walks_upward(project: Path) -> None:
    nested = project / "src" / "deep" / "nested"
    nested.mkdir(parents=True)
    assert find_project_root(nested) == project.resolve()


# spec: cli requirement=project-root-discovery scenario=sibling-shablon-is-not-discovered
def test_sibling_project_invisible(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    other = tmp_path / "other"
    (proj / ".shablon" / "templates").mkdir(parents=True)
    other.mkdir()
    with pytest.raises(ShablonError, match="no .shablon/"):
        find_project_root(other)


# spec: cli requirement=missing-configuration-errors-cleanly scenario=no-shablon-anywhere-on-the-path
def test_no_shablon_anywhere_errors(tmp_path: Path) -> None:
    with pytest.raises(ShablonError, match="no .shablon/"):
        find_project_root(tmp_path)


# --- template discovery --------------------------------------------------


def _names(paths: list[Path], root: Path) -> list[str]:
    return [str(p.relative_to(root)).replace("\\", "/") for p in paths]


# spec: templates requirement=partials-directories-are-partials-only scenario=top-level-partials-directory
# spec: templates requirement=partials-directories-are-partials-only scenario=nested-partials-directory
def test_partials_directory_excluded_at_any_depth(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "_includes/header.md", "shared")
    write(root / "skills/foo/SKILL.md", "x")
    write(root / "skills/foo/_includes/footer.md", "more shared")

    found = find_templates(root, [], "_includes")

    assert _names(found, root) == ["skills/foo/SKILL.md"]


# spec: templates requirement=partials-directories-are-partials-only scenario=custom-partials-directory-frees-the-default-name
def test_custom_partials_dir_frees_default_name(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "_partials/header.md", "shared")
    write(root / "_includes/note.md", "this should render")

    found = find_templates(root, [], "_partials")

    assert _names(found, root) == ["_includes/note.md"]


# spec: templates requirement=dotfiles-skipped-by-default scenario=mac-noise-file
def test_dotfile_skipped_by_default(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "skills/foo/SKILL.md", "x")
    write(root / "skills/foo/.DS_Store", "binary noise")

    found = find_templates(root, [], "_includes")

    assert _names(found, root) == ["skills/foo/SKILL.md"]


# spec: templates requirement=dotfiles-skipped-by-default scenario=re-included-via-config
def test_dotfile_reincluded_by_pattern(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "skills/foo/.gitignore", "node_modules\n")

    found = find_templates(root, [".gitignore"], "_includes")

    assert _names(found, root) == ["skills/foo/.gitignore"]


def test_dotfile_dir_is_not_descended(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / ".hidden/secret.md", "x")
    write(root / "visible.md", "y")

    found = find_templates(root, [], "_includes")

    assert _names(found, root) == ["visible.md"]


# spec: templates requirement=partials-directories-are-partials-only scenario=dotfile-inside-the-partials-directory-does-not-render-even-if-matched-by-include
def test_dotfile_in_partials_dir_stays_excluded(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "_includes/.partial.md", "fragment")

    found = find_templates(root, [".partial.md"], "_includes")

    assert _names(found, root) == []


# spec: templates requirement=deterministic-render-order scenario=stable-log-lines
def test_render_order_is_lexical(project: Path) -> None:
    root = project / ".shablon" / "templates"
    write(root / "b/x.md", "x")
    write(root / "a/y.md", "y")
    write(root / "a/z.md", "z")

    found = find_templates(root, [], "_includes")

    assert _names(found, root) == ["a/y.md", "a/z.md", "b/x.md"]


# spec: templates requirement=symlinks-are-followed scenario=symlinked-subtree
def test_symlinked_subtree_is_followed(tmp_path: Path) -> None:
    project = tmp_path / "proj"
    elsewhere = tmp_path / "elsewhere" / "shared"
    (project / ".shablon" / "templates").mkdir(parents=True)
    write(elsewhere / "notes.md", "shared content")

    link = project / ".shablon" / "templates" / "shared"
    link.symlink_to(elsewhere)

    root = project / ".shablon" / "templates"
    found = find_templates(root, [], "_includes")

    assert _names(found, root) == ["shared/notes.md"]
