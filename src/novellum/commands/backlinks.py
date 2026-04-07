"""Implementation of the ``novellum backlinks`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
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

    print(f"Note: {note.metadata.id}")
    print("Backlinks:")
    if not backlinks:
        print("- none")
        return 0

    for link in backlinks:
        if link.label:
            print(f"- {link.source_id} -> {note.metadata.id} [{link.label}]")
        else:
            print(f"- {link.source_id} -> {note.metadata.id}")
    return 0
