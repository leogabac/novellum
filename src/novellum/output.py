"""Shared Rich-based rendering helpers for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

from rich.box import SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
_PLAIN_OUTPUT = False
_JSON_OUTPUT = False


def set_plain_output(enabled: bool) -> None:
    """Toggle simplified non-Rich rendering for shared CLI output."""

    global _PLAIN_OUTPUT
    _PLAIN_OUTPUT = enabled


def set_json_output(enabled: bool) -> None:
    """Toggle JSON rendering for machine-readable CLI output."""

    global _JSON_OUTPUT
    _JSON_OUTPUT = enabled


def json_output_enabled() -> bool:
    """Return whether machine-readable JSON output is enabled."""

    return _JSON_OUTPUT


def emit_json(payload: object) -> None:
    """Serialize a JSON payload to stdout."""

    print(json.dumps(payload, indent=2, sort_keys=True))


def emit_error_json(*, code: str, message: str, details: dict[str, object] | None = None) -> None:
    """Emit a structured error payload for machine-readable clients."""

    payload: dict[str, object] = {
        "ok": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details:
        payload["error"]["details"] = details
    emit_json(payload)


def note_payload(note, *, workspace_root: Path, include_body: bool = False, include_links: bool = True) -> dict[str, object]:
    """Convert a note object into a stable JSON payload."""

    payload: dict[str, object] = {
        "id": note.metadata.id,
        "title": note.metadata.title,
        "type": note.metadata.note_type,
        "path": str(note.path.relative_to(workspace_root)),
        "created": note.metadata.created,
        "updated": note.metadata.updated,
        "tags": list(note.metadata.tags),
        "aliases": list(note.metadata.aliases),
    }
    if include_links:
        payload["link_count"] = len(note.links)
    if include_body:
        payload["body"] = note.body.rstrip()
    return payload


def indexed_link_payload(link) -> dict[str, object]:
    """Convert an indexed link into a stable JSON payload."""

    payload: dict[str, object] = {
        "source_id": link.source_id,
        "target": link.target,
        "resolved_id": link.resolved_id,
        "label": link.label,
        "candidate_ids": list(link.candidate_ids or []),
    }
    payload["kind"] = "resolved" if link.resolved_id is not None else ("ambiguous" if link.candidate_ids else "missing")
    return payload


def print_empty(message: str) -> None:
    """Render a muted message for empty command results."""

    if _PLAIN_OUTPUT:
        print(message)
        return
    console.print(f"[dim]{message}[/dim]")


def print_note_table(
    *,
    title: str,
    notes: list,
    workspace_root: Path,
    include_links: bool = True,
) -> None:
    """Render a note collection as a compact table plus summary."""

    if _PLAIN_OUTPUT:
        headers = ["ID", "TYPE", "TITLE"]
        if include_links:
            headers.append("LINKS")
        headers.append("PATH")
        print(title)
        print("\t".join(headers))
        for note in notes:
            row = [
                note.metadata.id,
                note.metadata.note_type,
                note.metadata.title,
            ]
            if include_links:
                row.append(str(len(note.links)))
            row.append(str(note.path.relative_to(workspace_root)))
            print("\t".join(row))
        print(f"{len(notes)} note(s)")
        return

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

    if _PLAIN_OUTPUT:
        print(title)
        for key, value in rows:
            print(f"{key}: {value}")
        return

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

    if _PLAIN_OUTPUT:
        print(title)
        print("\t".join(columns))
        for row in rows:
            print("\t".join(row))
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
