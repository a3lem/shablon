from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from shablon import generate
from shablon.errors import ShablonError

logger = logging.getLogger("shablon")


def main(argv: list[str] | None = None) -> int:
    _configure_logging()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help(sys.stderr)
        return 1

    try:
        assert args.command == "generate", args.command
        assert isinstance(args.cwd, Path), type(args.cwd)
        generate.run(start=args.cwd)
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
        "--cwd",
        type=Path,
        default=Path.cwd(),
        help="Starting directory for upward .shablon/ discovery (default: cwd).",
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
    return parser
