"""Implementation of the ``novellum edit`` command."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import subprocess

from novellum.index import find_note, load_index
from novellum.storage import find_workspace


def edit_command(reference: str, cwd: Path = Path(".")) -> int:
    """Open a note in the user's configured editor.

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

    editor = os.environ.get("EDITOR", "").strip()
    if not editor:
        raise RuntimeError("The $EDITOR environment variable is not set.")

    command = [*shlex.split(editor), str(note.path)]
    subprocess.run(command, check=True, cwd=workspace.root)
    return 0
