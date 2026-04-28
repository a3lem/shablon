from __future__ import annotations

import stat
from pathlib import Path


def write(path: Path, content: str = "", *, executable: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        make_executable(path)
    return path


def make_executable(path: Path) -> None:
    mode = path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    path.chmod(mode)


def vars_script(shablon_dir: Path, ext: str, body: str) -> Path:
    path = shablon_dir / f"vars.{ext}"
    path.write_text(body, encoding="utf-8")
    make_executable(path)
    return path
