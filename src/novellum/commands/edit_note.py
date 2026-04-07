"""Implementation of the ``novellum edit`` command."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import subprocess

from novellum.index import find_note, load_index
from novellum.selection import select_note_reference
from novellum.storage import find_workspace


def edit_command(
    reference: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Open a note in the user's configured editor.

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

    editor = os.environ.get("EDITOR", "").strip()
    if not editor:
        raise RuntimeError("The $EDITOR environment variable is not set.")

    open_in_editor(note.path, workspace.root)
    return 0


def open_in_editor(note_path: Path, workspace_root: Path) -> None:
    """Open a note path with the configured ``$EDITOR`` command."""

    editor = os.environ.get("EDITOR", "").strip()
    if not editor:
        raise RuntimeError("The $EDITOR environment variable is not set.")

    command = [*shlex.split(editor), str(note_path)]
    subprocess.run(command, check=True, cwd=workspace_root)
