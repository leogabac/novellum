"""Implementation of the ``novellum delete`` command."""

from __future__ import annotations

from pathlib import Path

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.selection import select_note_reference
from novellum.storage import delete_note, find_workspace


def delete_command(
    reference: str | None = None,
    *,
    force: bool = False,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Delete a note file from the workspace."""

    logger = get_cli_logger("novellum.delete")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    note = find_note(index, resolved_reference)
    if not force:
        if not interactive:
            raise ValueError("Pass --yes to confirm deletion in non-interactive mode.")
        confirmed = _confirm_delete(note.metadata.id, note.metadata.title)
        if not confirmed:
            raise RuntimeError("Deletion cancelled.")

    deleted_path = delete_note(workspace, resolved_reference, source_path=note.path)
    logger.info("Deleted note %s", deleted_path.relative_to(workspace.root))
    return 0


def _confirm_delete(note_id: str, title: str) -> bool:
    """Prompt for delete confirmation via questionary."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    return bool(questionary.confirm(f"Delete {note_id} ({title})?", default=False).ask())
