"""Implementation of the ``novellum show`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.storage import find_workspace


def show_command(reference: str, cwd: Path = Path(".")) -> int:
    """Display a note resolved by canonical ID or alias.

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

    print(f"ID: {note.metadata.id}")
    print(f"Title: {note.metadata.title}")
    print(f"Type: {note.metadata.note_type}")
    print(f"Path: {note.path.relative_to(workspace.root)}")
    print(f"Tags: {', '.join(note.metadata.tags) if note.metadata.tags else '-'}")
    print(f"Aliases: {', '.join(note.metadata.aliases) if note.metadata.aliases else '-'}")
    print(f"Links: {len(note.links)}")
    print("")
    print(note.body.rstrip())
    return 0
