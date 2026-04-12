"""Implementation of the ``novellum show`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.output import console, emit_json, json_output_enabled, note_payload, print_key_value_panel
from novellum.selection import select_note_reference
from novellum.storage import find_workspace


def show_command(
    reference: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Display a note resolved by canonical ID or alias.

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

    if json_output_enabled():
        emit_json(
            {
                "ok": True,
                "command": "show",
                "workspace_root": str(workspace.root),
                "note": note_payload(note, workspace_root=workspace.root, include_body=True),
            }
        )
        return 0

    print_key_value_panel(
        f"Note: {note.metadata.id}",
        [
            ("ID", note.metadata.id),
            ("Title", note.metadata.title),
            ("Type", note.metadata.note_type),
            ("Path", str(note.path.relative_to(workspace.root))),
            ("Tags", ", ".join(note.metadata.tags) if note.metadata.tags else "-"),
            ("Aliases", ", ".join(note.metadata.aliases) if note.metadata.aliases else "-"),
            ("Links", str(len(note.links))),
        ],
    )
    console.print(note.body.rstrip())
    return 0
