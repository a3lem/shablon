from __future__ import annotations

import fnmatch
from pathlib import Path, PurePosixPath

from shablon.errors import ShablonError


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    assert current.is_absolute(), current
    while True:
        if (current / ".shablon").is_dir():
            return current
        if current.parent == current:
            raise ShablonError(
                f"no .shablon/ found at {start} or any ancestor"
            )
        current = current.parent


def find_templates(
    template_root: Path,
    include_patterns: list[str],
    partials_dir: str,
) -> list[Path]:
    results: list[Path] = []
    for path in template_root.rglob("*", recurse_symlinks=True):
        if not path.is_file():
            continue
        rel = path.relative_to(template_root)
        if _is_excluded(rel, include_patterns, partials_dir):
            continue
        results.append(path)

    results.sort(key=lambda p: PurePosixPath(p.relative_to(template_root)).as_posix())
    return results


def _is_excluded(
    rel: Path,
    include_patterns: list[str],
    partials_dir: str,
) -> bool:
    parents = rel.parts[:-1]
    basename = rel.parts[-1]

    for part in parents:
        if part == partials_dir:
            return True
        if part.startswith("."):
            return True

    if basename.startswith("."):
        for pattern in include_patterns:
            if fnmatch.fnmatchcase(basename, pattern):
                return False
        return True

    return False
