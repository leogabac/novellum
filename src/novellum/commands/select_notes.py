"""Implementation of the ``novellum select`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import load_index
from novellum.selection import select_note_references_iterative
from novellum.storage import find_workspace


def select_command(cwd: Path = Path(".")) -> int:
    """Iteratively select notes and print their IDs on stdout.

    Parameters
    ----------
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    selected_ids = select_note_references_iterative(index)
    if selected_ids is None:
        raise RuntimeError("Interactive selection requires fzf to be installed.")
    for note_id in selected_ids:
        print(note_id)
    return 0
