"""Implementation of the ``novellum search`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import load_index, search_notes
from novellum.output import print_empty, print_note_table
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
        print_empty("No notes found.")
        return 0

    print_note_table(
        title=f"Search Results: {query}",
        notes=matches,
        workspace_root=workspace.root,
        include_links=False,
    )
    return 0
