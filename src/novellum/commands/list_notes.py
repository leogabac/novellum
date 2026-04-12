"""Implementation of the ``novellum list`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import load_index
from novellum.output import emit_json, json_output_enabled, note_payload, print_empty, print_note_table
from novellum.storage import find_workspace


def list_command(
    note_type: str | None = None,
    cwd: Path = Path("."),
) -> int:
    """List notes in the workspace, optionally filtered by category.

    Parameters
    ----------
    note_type : str or None, optional
        Restrict output to a single note category.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    notes = sorted(
        (
            note
            for note in index.notes_by_id.values()
            if note_type is None or note.metadata.note_type == note_type
        ),
        key=lambda note: note.path,
    )

    if not notes:
        if json_output_enabled():
            emit_json(
                {
                    "ok": True,
                    "command": "list",
                    "workspace_root": str(workspace.root),
                    "type": note_type,
                    "notes": [],
                }
            )
            return 0
        print_empty("No notes found.")
        return 0

    if json_output_enabled():
        emit_json(
            {
                "ok": True,
                "command": "list",
                "workspace_root": str(workspace.root),
                "type": note_type,
                "notes": [note_payload(note, workspace_root=workspace.root) for note in notes],
            }
        )
        return 0

    title = "Notes"
    if note_type:
        title = f"Notes ({note_type})"
    print_note_table(title=title, notes=notes, workspace_root=workspace.root, include_links=True)
    return 0
