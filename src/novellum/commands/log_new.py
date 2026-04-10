"""Implementation of the ``novellum log new`` command."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from novellum.index import load_index
from novellum.storage import create_note, find_workspace


def log_new_command(
    title: str | None = None,
    log_date: str | None = None,
    cwd: Path = Path("."),
) -> int:
    """Create a dated research log note.

    Parameters
    ----------
    title : str or None, optional
        Optional human-readable title. Defaults to the log date.
    log_date : str or None, optional
        Explicit ISO date in ``YYYY-MM-DD`` form. Defaults to today.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    resolved_date = _resolve_log_date(log_date)
    note_id = f"log-{resolved_date.isoformat()}"
    index = load_index(workspace)
    existing_note = index.notes_by_id.get(note_id)
    if existing_note is not None:
        print(f"Log note already exists at {existing_note.path.relative_to(workspace.root)}")
        print(f"ID: {existing_note.metadata.id}")
        return 0

    note_path = create_note(
        workspace,
        title=title or resolved_date.isoformat(),
        note_type="log",
        note_id=note_id,
        tags=["log", resolved_date.isoformat()],
        aliases=[resolved_date.isoformat(), "today"] if resolved_date == date.today() else [resolved_date.isoformat()],
    )
    print(f"Created log note {note_path.relative_to(workspace.root)}")
    return 0


def _resolve_log_date(log_date: str | None) -> date:
    """Parse a log date or default to the current local date."""

    if log_date is None:
        return date.today()
    try:
        return date.fromisoformat(log_date)
    except ValueError as error:
        raise ValueError("Log date must use YYYY-MM-DD format.") from error
