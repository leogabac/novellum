"""Implementation of the ``novellum today`` command."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from novellum.commands.edit_note import open_in_editor
from novellum.storage import create_note, find_workspace, find_note_path_by_id


def today_command(cwd: Path = Path(".")) -> int:
    """Open today's research log note, creating it if necessary.

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
    today_value = date.today().isoformat()
    note_id = f"log-{today_value}"
    note_path = find_note_path_by_id(workspace, note_id)

    if note_path is None:
        note_path = create_note(
            workspace,
            title=today_value,
            note_type="log",
            note_id=note_id,
            tags=["log", today_value],
            aliases=[today_value, "today"],
        )
        print(f"Created log note {note_path.relative_to(workspace.root)}")

    open_in_editor(note_path, workspace.root)
    return 0
