from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from shablon.errors import ShablonError

_VALID_KEYS = {"include", "partials_dir"}


@dataclass(frozen=True)
class Config:
    include: list[str] = field(default_factory=list)
    partials_dir: str = "_includes"


def load(shablon_dir: Path) -> Config:
    path = shablon_dir / "config.toml"
    if not path.exists():
        return Config()

    text = path.read_text(encoding="utf-8")
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ShablonError(f"failed to parse {path}: {exc}") from exc

    unknown = sorted(set(parsed) - _VALID_KEYS)
    if unknown:
        raise ShablonError(
            f"{path}: unknown top-level key(s): {', '.join(unknown)}"
        )

    if "include" in parsed:
        include = parsed["include"]
        if not isinstance(include, list) or not all(isinstance(s, str) for s in include):
            raise ShablonError(
                f"{path}: field 'include' must be an array of strings"
            )
    else:
        include = []

    if "partials_dir" in parsed:
        partials_dir = parsed["partials_dir"]
    else:
        partials_dir = "_includes"
    if not isinstance(partials_dir, str) or not partials_dir:
        raise ShablonError(
            f"{path}: field 'partials_dir' must be a non-empty string "
            f"(got {partials_dir!r})"
        )
    if "/" in partials_dir or "\\" in partials_dir:
        raise ShablonError(
            f"{path}: field 'partials_dir' must not contain path separators "
            f"(got {partials_dir!r})"
        )
    if partials_dir in (".", ".."):
        raise ShablonError(
            f"{path}: field 'partials_dir' must not be '.' or '..' "
            f"(got {partials_dir!r})"
        )

    return Config(include=list(include), partials_dir=partials_dir)
