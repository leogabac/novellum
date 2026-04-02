"""Implementation of the ``novellum new`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.storage import create_note, find_workspace


def new_command(
    title: str,
    note_type: str = "concept",
    note_id: str | None = None,
    tags: list[str] | None = None,
    alias: list[str] | None = None,
    cwd: Path = Path("."),
) -> int:
    """Create a new note in the current workspace.

    Parameters
    ----------
    title : str
        Note title.
    note_type : str, optional
        Note category.
    note_id : str or None, optional
        Explicit stable note identifier.
    tags : list[str] or None, optional
        Tags stored in metadata.
    alias : list[str] or None, optional
        Alternate note references stored in metadata.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    note_path = create_note(
        workspace,
        title=title,
        note_type=note_type,
        note_id=note_id,
        tags=tags,
        aliases=alias,
    )
    print(f"Created note {note_path.relative_to(workspace.root)}")
    return 0
