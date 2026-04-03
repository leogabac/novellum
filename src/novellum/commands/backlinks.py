"""Implementation of the ``novellum backlinks`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.storage import find_workspace


def backlinks_command(reference: str, cwd: Path = Path(".")) -> int:
    """Display inbound links for a resolved note.

    Parameters
    ----------
    reference : str
        Note ID or alias.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    note = find_note(index, reference)
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
