"""Implementation of the ``novellum backlinks`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.output import emit_json, indexed_link_payload, json_output_enabled, print_key_value_panel, print_link_table
from novellum.selection import select_note_reference
from novellum.storage import find_workspace


def backlinks_command(
    reference: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Display inbound links for a resolved note.

    Parameters
    ----------
    reference : str or None, optional
        Note ID or alias. When omitted, interactive selection is attempted.
    interactive : bool, optional
        Whether interactive note selection should be attempted when the
        reference is omitted.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")
    note = find_note(index, resolved_reference)
    backlinks = index.backlinks[note.metadata.id]

    if json_output_enabled():
        emit_json(
            {
                "ok": True,
                "command": "backlinks",
                "workspace_root": str(workspace.root),
                "note": {
                    "id": note.metadata.id,
                    "title": note.metadata.title,
                    "type": note.metadata.note_type,
                    "path": str(note.path.relative_to(workspace.root)),
                },
                "backlinks": [indexed_link_payload(link) for link in backlinks],
            }
        )
        return 0

    print_key_value_panel(
        f"Backlinks: {note.metadata.id}",
        [
            ("Note", note.metadata.id),
            ("Inbound Links", str(len(backlinks))),
        ],
    )
    rows = [
        (
            link.source_id,
            note.metadata.id,
            link.label or "-",
        )
        for link in backlinks
    ]
    print_link_table(
        "Backlinks",
        rows,
        empty_message="No backlinks found.",
        columns=["Source", "Resolved", "Label"],
    )
    return 0
