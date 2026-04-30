from __future__ import annotations

import enum
import typing as T
from pathlib import Path, PurePosixPath

from jinja2 import Environment, FileSystemLoader


class RenderOutcome(enum.Enum):
    WROTE = "wrote"
    UNCHANGED = "unchanged"


def build_env(template_root: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(template_root),
        keep_trailing_newline=True,
    )


# [AI]
# Context: report-render-changes (skip rewrite when content+mode already match)
# Intent: callers print 'wrote' vs 'unchanged' based on the returned outcome
def render_to_file(
    env: Environment,
    template_rel: PurePosixPath,
    output_path: Path,
    context: dict[str, T.Any],
    source_path: Path,
) -> RenderOutcome:
    template = env.get_template(str(template_rel))
    rendered = template.render(**context)
    rendered_bytes = rendered.encode("utf-8")
    intended_mode = source_path.stat().st_mode & 0o777

    if output_path.exists():
        existing_bytes = output_path.read_bytes()
        existing_mode = output_path.stat().st_mode & 0o777
        if existing_bytes == rendered_bytes and existing_mode == intended_mode:
            return RenderOutcome.UNCHANGED
        if existing_bytes != rendered_bytes:
            _ = output_path.write_bytes(rendered_bytes)
        if existing_mode != intended_mode:
            output_path.chmod(intended_mode)
        return RenderOutcome.WROTE

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _ = output_path.write_bytes(rendered_bytes)
    output_path.chmod(intended_mode)
    return RenderOutcome.WROTE
