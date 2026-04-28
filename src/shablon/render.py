from __future__ import annotations

import typing as T
from pathlib import Path, PurePosixPath

from jinja2 import Environment, FileSystemLoader


def build_env(template_root: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_root),
        keep_trailing_newline=True,
    )


def render_to_file(
    env: Environment,
    template_rel: PurePosixPath,
    output_path: Path,
    context: dict[str, T.Any],
    source_path: Path,
) -> None:
    template = env.get_template(str(template_rel))
    rendered = template.render(**context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    mode = source_path.stat().st_mode & 0o777
    output_path.chmod(mode)
