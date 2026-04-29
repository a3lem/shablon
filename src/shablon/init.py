from __future__ import annotations

from pathlib import Path

from shablon.errors import ShablonError

_CONFIG_TOML = """\
# Shablon configuration. Uncomment to override defaults.
#
# include = []
# partials_dir = "_includes"
"""

_VARS_SH = """\
#!/usr/bin/env sh
# Print the render context as a JSON object on stdout.
echo '{}'
"""


def run(target: Path) -> None:
    assert target.is_absolute(), target
    assert target.is_dir(), target

    shablon_dir = target / ".shablon"
    if shablon_dir.exists() or shablon_dir.is_symlink():
        raise ShablonError(
            f"{shablon_dir} already exists; refusing to overwrite"
        )

    shablon_dir.mkdir()
    (shablon_dir / "templates").mkdir()
    (shablon_dir / "templates" / "_includes").mkdir()

    (shablon_dir / "config.toml").write_text(_CONFIG_TOML, encoding="utf-8")

    vars_path = shablon_dir / "vars.sh"
    vars_path.write_text(_VARS_SH, encoding="utf-8")
    vars_path.chmod(0o755)

    print(f"initialized {shablon_dir}")
