"""Implementation of the ``novellum search`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import load_index, search_notes
from novellum.storage import find_workspace


def search_command(query: str, cwd: Path = Path(".")) -> int:
    """Search notes by metadata and body text.

    Parameters
    ----------
    query : str
        Case-insensitive search term.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    matches = search_notes(index, query)

    if not matches:
        print("No notes found.")
        return 0

    print("ID\tTYPE\tTITLE\tPATH")
    for note in matches:
        print(
            "\t".join(
                [
                    note.metadata.id,
                    note.metadata.note_type,
                    note.metadata.title,
                    str(note.path.relative_to(workspace.root)),
                ]
            )
        )
    return 0
