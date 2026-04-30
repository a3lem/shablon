from __future__ import annotations

from pathlib import Path, PurePosixPath

from shablon import config, discovery, render, variables
from shablon.errors import ShablonError


def run(start: Path) -> None:
    project_root = discovery.find_project_root(start)
    shablon_dir = project_root / ".shablon"
    template_root = shablon_dir / "templates"
    if not template_root.is_dir():
        raise ShablonError(
            f"{template_root} not found; .shablon/templates/ is required"
        )

    cfg = config.load(shablon_dir)
    context = variables.resolve(shablon_dir)
    env = render.build_env(template_root)
    templates = discovery.find_templates(template_root, cfg.include, cfg.partials_dir)

    for template_path in templates:
        rel = PurePosixPath(template_path.relative_to(template_root).as_posix())
        assert not rel.is_absolute(), rel
        output_path = project_root / Path(*rel.parts)
        outcome = render.render_to_file(env, rel, output_path, context, template_path)
        print(f"{outcome.value} {rel}")
