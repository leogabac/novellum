from __future__ import annotations

import argparse
from pathlib import Path

from novellum.commands.init import init_command
from novellum.commands.list_notes import list_command
from novellum.commands.new_note import new_command

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="novellum", description="A CLI for linked LaTeX research notes.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a novellum workspace.")
    init_parser.add_argument("path", nargs="?", default=".")

    new_parser = subparsers.add_parser("new", help="Create a new note.")
    new_parser.add_argument("title")
    new_parser.add_argument("--type", "-t", default="concept", dest="note_type")
    new_parser.add_argument("--id", dest="note_id")
    new_parser.add_argument("--tag", action="append", default=None, dest="tags")
    new_parser.add_argument("--alias", action="append", default=None)
    new_parser.add_argument("--cwd", default=".")

    list_parser = subparsers.add_parser("list", help="List notes.")
    list_parser.add_argument("--type", "-t", default=None, dest="note_type")
    list_parser.add_argument("--cwd", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return init_command(Path(args.path))
    if args.command == "new":
        return new_command(
            title=args.title,
            note_type=args.note_type,
            note_id=args.note_id,
            tags=args.tags,
            alias=args.alias,
            cwd=Path(args.cwd),
        )
    if args.command == "list":
        return list_command(note_type=args.note_type, cwd=Path(args.cwd))
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
