from __future__ import annotations

import json
import os
import re
import subprocess
import typing as T
from pathlib import Path

from shablon.errors import ShablonError

_VARS_PATTERN = re.compile(r"^vars\.[^./]+$")


def resolve(shablon_dir: Path) -> dict[str, T.Any]:
    candidates = _find_vars_files(shablon_dir)
    if not candidates:
        return {}
    if len(candidates) > 1:
        names = ", ".join(sorted(p.name for p in candidates))
        raise ShablonError(
            f"more than one vars.<ext> file in {shablon_dir}: {names}"
        )

    script = candidates[0]
    if not os.access(script, os.X_OK):
        raise ShablonError(
            f"{script} is not executable; run `chmod +x {script}` to fix"
        )

    project_root = shablon_dir.parent
    env = {**os.environ, "SHABLON_PROJECT_ROOT": str(project_root)}

    result = subprocess.run(
        [str(script)],
        cwd=project_root,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        check=False,
    )

    if result.returncode != 0:
        raise ShablonError(
            f"{script.name} exited with status {result.returncode}"
        )

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ShablonError(
            f"{script} produced invalid JSON on stdout: {exc}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ShablonError(
            f"{script} must print a JSON object to stdout, got "
            f"{type(parsed).__name__}"
        )

    return parsed


def _find_vars_files(shablon_dir: Path) -> list[Path]:
    if not shablon_dir.is_dir():
        return []
    return [
        entry
        for entry in shablon_dir.iterdir()
        if entry.is_file() and _VARS_PATTERN.match(entry.name)
    ]
