"""Shared Rich-based rendering helpers for CLI commands."""

from __future__ import annotations

from pathlib import Path

from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_empty(message: str) -> None:
    """Render a muted message for empty command results."""

    console.print(f"[dim]{message}[/dim]")


def print_note_table(
    *,
    title: str,
    notes: list,
    workspace_root: Path,
    include_links: bool = True,
) -> None:
    """Render a note collection as a compact table plus summary."""

    table = Table(title=title, box=SIMPLE_HEAVY, header_style="bold cyan", row_styles=["", "dim"])
    table.add_column("ID", style="bold")
    table.add_column("Type", style="magenta")
    table.add_column("Title", overflow="fold")
    if include_links:
        table.add_column("Links", justify="right", style="green")
    table.add_column("Path", style="dim", overflow="fold")

    for note in notes:
        row = [
            note.metadata.id,
            note.metadata.note_type,
            note.metadata.title,
        ]
        if include_links:
            row.append(str(len(note.links)))
        row.append(str(note.path.relative_to(workspace_root)))
        table.add_row(*row)

    console.print(table)
    console.print(f"[dim]{len(notes)} note(s)[/dim]")


def print_key_value_panel(title: str, rows: list[tuple[str, str]]) -> None:
    """Render key-value note metadata as a two-column table in a panel."""

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column(overflow="fold")
    for key, value in rows:
        table.add_row(key, value)
    console.print(Panel(table, title=title, border_style="cyan"))


def print_link_table(title: str, rows: list[tuple[str, ...]], *, empty_message: str, columns: list[str]) -> None:
    """Render graph diagnostics in a consistent table layout."""

    if not rows:
        print_empty(empty_message)
        return

    table = Table(title=title, box=SIMPLE_HEAVY, header_style="bold cyan", row_styles=["", "dim"])
    for column in columns:
        if column.lower() in {"kind", "type"}:
            table.add_column(column, style="magenta")
        elif column.lower() in {"source", "resolved"}:
            table.add_column(column, style="green")
        else:
            table.add_column(column, overflow="fold")
    for row in rows:
        table.add_row(*row)
    console.print(table)
