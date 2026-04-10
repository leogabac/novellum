"""Command-line entrypoint for Novellum.

The CLI currently uses the standard library ``argparse`` module to keep the
runtime dependency footprint low while the command surface is still small.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from novellum.commands.backlinks import backlinks_command
from novellum.commands.alias_note import alias_add_command, alias_remove_command
from novellum.commands.broken_links import broken_command
from novellum.commands.compile_document import compile_command
from novellum.commands.delete_note import delete_command
from novellum.commands.edit_note import edit_command
from novellum.commands.graph_view import graph_command
from novellum.commands.init import init_command
from novellum.commands.links import links_command
from novellum.commands.list_notes import list_command
from novellum.commands.log_new import log_new_command
from novellum.commands.move_note import move_command
from novellum.commands.new_note import new_command
from novellum.commands.open_document import open_command
from novellum.commands.rename_note import rename_command
from novellum.commands.retag_note import retag_command
from novellum.commands.select_notes import select_command
from novellum.commands.search_notes import search_command
from novellum.commands.show_note import show_command
from novellum.commands.stitch_notes import stitch_command
from novellum.commands.tag_note import tag_add_command, tag_remove_command
from novellum.commands.today import today_command
from novellum.output import set_plain_output
from novellum.storage import DEFAULT_NOTE_TYPES


_STITCH_CATEGORY_FLAGS = {
    "concept": "--concepts",
    "proof": "--proofs",
    "paper": "--papers",
    "experiment": "--experiments",
    "question": "--questions",
    "log": "--logs",
    "ref": "--refs",
}


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured with all supported subcommands.
    """

    parser = argparse.ArgumentParser(prog="novellum", description="A CLI for linked LaTeX research notes.")
    parser.add_argument("--plain", action="store_true", help="Disable Rich-styled output and use plain text.")
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

    retag_parser = subparsers.add_parser("retag", help="Replace a note's tag list.")
    retag_parser.add_argument("reference", nargs="?")
    retag_parser.add_argument("--tag", action="append", default=None, dest="tags")
    retag_parser.add_argument("--no-interactive", action="store_true")
    retag_parser.add_argument("--cwd", default=".")

    tag_parser = subparsers.add_parser("tag", help="Add or remove note tags.")
    tag_subparsers = tag_parser.add_subparsers(dest="tag_command", required=True)
    tag_add_parser = tag_subparsers.add_parser("add", help="Add a tag to a note.")
    tag_add_parser.add_argument("reference", nargs="?")
    tag_add_parser.add_argument("tag_value", nargs="?")
    tag_add_parser.add_argument("--no-interactive", action="store_true")
    tag_add_parser.add_argument("--cwd", default=".")
    tag_remove_parser = tag_subparsers.add_parser("remove", help="Remove a tag from a note.")
    tag_remove_parser.add_argument("reference", nargs="?")
    tag_remove_parser.add_argument("tag_value", nargs="?")
    tag_remove_parser.add_argument("--no-interactive", action="store_true")
    tag_remove_parser.add_argument("--cwd", default=".")

    alias_parser = subparsers.add_parser("alias", help="Add or remove note aliases.")
    alias_subparsers = alias_parser.add_subparsers(dest="alias_command", required=True)
    alias_add_parser = alias_subparsers.add_parser("add", help="Add an alias to a note.")
    alias_add_parser.add_argument("reference", nargs="?")
    alias_add_parser.add_argument("alias_value", nargs="?")
    alias_add_parser.add_argument("--no-interactive", action="store_true")
    alias_add_parser.add_argument("--cwd", default=".")
    alias_remove_parser = alias_subparsers.add_parser("remove", help="Remove an alias from a note.")
    alias_remove_parser.add_argument("reference", nargs="?")
    alias_remove_parser.add_argument("alias_value", nargs="?")
    alias_remove_parser.add_argument("--no-interactive", action="store_true")
    alias_remove_parser.add_argument("--cwd", default=".")

    rename_parser = subparsers.add_parser("rename", help="Rename a note ID and file.")
    rename_parser.add_argument("reference", nargs="?")
    rename_parser.add_argument("new_note_id", nargs="?")
    rename_parser.add_argument("--dry-run", action="store_true")
    rename_parser.add_argument("--no-rewrite-links", action="store_true")
    rename_parser.add_argument("--no-interactive", action="store_true")
    rename_parser.add_argument("--cwd", default=".")

    move_parser = subparsers.add_parser("move", help="Move a note to another note type.")
    move_parser.add_argument("reference", nargs="?")
    move_parser.add_argument("new_note_type", nargs="?")
    move_parser.add_argument("--no-interactive", action="store_true")
    move_parser.add_argument("--cwd", default=".")

    delete_parser = subparsers.add_parser("delete", help="Delete a note file.")
    delete_parser.add_argument("reference", nargs="?")
    delete_parser.add_argument("--yes", action="store_true", dest="force")
    delete_parser.add_argument("--no-interactive", action="store_true")
    delete_parser.add_argument("--cwd", default=".")

    list_parser = subparsers.add_parser("list", aliases=["ls"], help="List notes.")
    list_parser.add_argument("--type", "-t", default=None, dest="note_type")
    list_parser.add_argument("--cwd", default=".")

    show_parser = subparsers.add_parser("show", help="Show a note.")
    show_parser.add_argument("reference", nargs="?")
    show_parser.add_argument("--no-interactive", action="store_true")
    show_parser.add_argument("--cwd", default=".")

    edit_parser = subparsers.add_parser("edit", help="Open a note in $EDITOR.")
    edit_parser.add_argument("reference", nargs="?")
    edit_parser.add_argument("--no-interactive", action="store_true")
    edit_parser.add_argument("--cwd", default=".")

    links_parser = subparsers.add_parser("links", help="Show note links.")
    links_parser.add_argument("reference", nargs="?")
    links_parser.add_argument("--no-interactive", action="store_true")
    links_parser.add_argument("--cwd", default=".")

    backlinks_parser = subparsers.add_parser("backlinks", help="Show inbound links to a note.")
    backlinks_parser.add_argument("reference", nargs="?")
    backlinks_parser.add_argument("--no-interactive", action="store_true")
    backlinks_parser.add_argument("--cwd", default=".")

    broken_parser = subparsers.add_parser("broken", help="Show unresolved or ambiguous links.")
    broken_parser.add_argument("--cwd", default=".")

    search_parser = subparsers.add_parser("search", help="Search notes.")
    search_parser.add_argument("query")
    search_parser.add_argument("--cwd", default=".")

    graph_parser = subparsers.add_parser("graph", help="Export the note graph as Mermaid.")
    graph_parser.add_argument("--type", "-t", default=None, dest="note_type")
    graph_parser.add_argument("--render", choices=["svg", "png", "pdf"], default=None, dest="render_format")
    graph_parser.add_argument("--output", default=None)
    graph_parser.add_argument("--cwd", default=".")

    stitch_parser = subparsers.add_parser("stitch", help="Generate a stitched LaTeX document from notes.")
    stitch_parser.add_argument("references", nargs="*")
    stitch_parser.add_argument("--all", action="store_true", dest="stitch_all")
    for note_type in DEFAULT_NOTE_TYPES:
        stitch_parser.add_argument(_STITCH_CATEGORY_FLAGS[note_type], action="store_true", dest=f"stitch_{note_type}")
    stitch_parser.add_argument("--no-interactive", action="store_true")
    stitch_parser.add_argument("--title", default="Novellum Stitch")
    stitch_parser.add_argument("--output", default=None)
    stitch_parser.add_argument("--cwd", default=".")

    compile_parser = subparsers.add_parser("compile", help="Compile a workspace or stitched LaTeX target.")
    compile_parser.add_argument("target", nargs="?", default="workspace")
    compile_parser.add_argument("--cwd", default=".")

    open_parser = subparsers.add_parser("open", help="Open a compiled PDF target in a viewer.")
    open_parser.add_argument("target", nargs="?", default="stitched")
    open_parser.add_argument("--cwd", default=".")

    select_parser = subparsers.add_parser("select", help="Interactively choose notes and print their IDs.")
    select_parser.add_argument("--cwd", default=".")

    log_parser = subparsers.add_parser("log", help="Create and manage research log notes.")
    log_subparsers = log_parser.add_subparsers(dest="log_command", required=True)
    log_new_parser = log_subparsers.add_parser("new", help="Create a dated research log note.")
    log_new_parser.add_argument("title", nargs="?")
    log_new_parser.add_argument("--date", dest="log_date", default=None)
    log_new_parser.add_argument("--cwd", default=".")

    today_parser = subparsers.add_parser("today", help="Open or create today's research log note.")
    today_parser.add_argument("--cwd", default=".")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Novellum CLI.

    Parameters
    ----------
    argv : list[str] or None, optional
        Explicit argument vector. When ``None``, arguments are read from the
        process command line.

    Returns
    -------
    int
        Process-style exit code.
    """

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        set_plain_output(args.plain)

        # Dispatch stays explicit instead of dynamic so command wiring is easy
        # to read while the CLI surface remains small.
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
        if args.command == "retag":
            return retag_command(
                reference=args.reference,
                tags=args.tags,
                interactive=not args.no_interactive,
                cwd=Path(args.cwd),
            )
        if args.command == "tag":
            if args.tag_command == "add":
                return tag_add_command(
                    reference=args.reference,
                    tag=args.tag_value,
                    interactive=not args.no_interactive,
                    cwd=Path(args.cwd),
                )
            if args.tag_command == "remove":
                return tag_remove_command(
                    reference=args.reference,
                    tag=args.tag_value,
                    interactive=not args.no_interactive,
                    cwd=Path(args.cwd),
                )
        if args.command == "alias":
            if args.alias_command == "add":
                return alias_add_command(
                    reference=args.reference,
                    alias=args.alias_value,
                    interactive=not args.no_interactive,
                    cwd=Path(args.cwd),
                )
            if args.alias_command == "remove":
                return alias_remove_command(
                    reference=args.reference,
                    alias=args.alias_value,
                    interactive=not args.no_interactive,
                    cwd=Path(args.cwd),
                )
        if args.command == "rename":
            return rename_command(
                reference=args.reference,
                new_note_id=args.new_note_id,
                rewrite_links=not args.no_rewrite_links,
                dry_run=args.dry_run,
                interactive=not args.no_interactive,
                cwd=Path(args.cwd),
            )
        if args.command == "move":
            return move_command(
                reference=args.reference,
                new_note_type=args.new_note_type,
                interactive=not args.no_interactive,
                cwd=Path(args.cwd),
            )
        if args.command == "delete":
            return delete_command(
                reference=args.reference,
                force=args.force,
                interactive=not args.no_interactive,
                cwd=Path(args.cwd),
            )
        if args.command in {"list", "ls"}:
            return list_command(note_type=args.note_type, cwd=Path(args.cwd))
        if args.command == "show":
            return show_command(reference=args.reference, interactive=not args.no_interactive, cwd=Path(args.cwd))
        if args.command == "edit":
            return edit_command(reference=args.reference, interactive=not args.no_interactive, cwd=Path(args.cwd))
        if args.command == "links":
            return links_command(reference=args.reference, interactive=not args.no_interactive, cwd=Path(args.cwd))
        if args.command == "backlinks":
            return backlinks_command(
                reference=args.reference,
                interactive=not args.no_interactive,
                cwd=Path(args.cwd),
            )
        if args.command == "broken":
            return broken_command(cwd=Path(args.cwd))
        if args.command == "search":
            return search_command(query=args.query, cwd=Path(args.cwd))
        if args.command == "graph":
            output_path = Path(args.output) if args.output else None
            return graph_command(
                note_type=args.note_type,
                render_format=args.render_format,
                output_path=output_path,
                cwd=Path(args.cwd),
            )
        if args.command == "stitch":
            output_path = Path(args.output) if args.output else None
            selected_types = [
                note_type
                for note_type in DEFAULT_NOTE_TYPES
                if getattr(args, f"stitch_{note_type}", False)
            ]
            return stitch_command(
                references=args.references,
                stitch_all=args.stitch_all,
                note_types=selected_types,
                interactive=not args.no_interactive,
                title=args.title,
                output_path=output_path,
                cwd=Path(args.cwd),
            )
        if args.command == "compile":
            return compile_command(target=args.target, cwd=Path(args.cwd))
        if args.command == "open":
            return open_command(target=args.target, cwd=Path(args.cwd))
        if args.command == "select":
            return select_command(cwd=Path(args.cwd))
        if args.command == "log":
            if args.log_command == "new":
                return log_new_command(title=args.title, log_date=args.log_date, cwd=Path(args.cwd))
        if args.command == "today":
            return today_command(cwd=Path(args.cwd))
        parser.error(f"Unknown command: {args.command}")
    except (FileExistsError, FileNotFoundError, LookupError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
