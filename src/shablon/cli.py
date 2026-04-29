from __future__ import annotations

import argparse
import logging
import sys
import typing as T
from pathlib import Path

from shablon import __version__, generate, init
from shablon.errors import ShablonError

logger = logging.getLogger("shablon")

_COMMANDS: dict[str, T.Callable[[Path], None]] = {
    "generate": generate.run,
    "init": init.run,
}


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help(sys.stderr)
        return 1

    try:
        assert args.command in _COMMANDS, args.command
        _COMMANDS[args.command](Path.cwd().resolve())
    except ShablonError as exc:
        logger.error("%s", exc)
        return 1

    return 0


def _configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    root = logging.getLogger("shablon")
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shablon",
        description="Render Jinja2 templates from .shablon/templates/.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"shablon {__version__}",
    )
    sub = parser.add_subparsers(
        dest="command",
        title="commands",
        metavar="<command>",
    )
    sub.add_parser(
        "generate",
        help="Render templates from .shablon/templates/.",
    )
    sub.add_parser(
        "init",
        help="Scaffold a new .shablon/ directory in the current working directory.",
    )
    return parser
