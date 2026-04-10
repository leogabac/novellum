"""Implementation of the ``novellum rename`` command."""

from __future__ import annotations

from pathlib import Path

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.selection import select_note_reference
from novellum.storage import find_workspace, rename_note


def rename_command(
    reference: str | None = None,
    new_note_id: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Rename a note ID and its backing file."""

    logger = get_cli_logger("novellum.rename")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    resolved_new_id = new_note_id
    if resolved_new_id is None and interactive:
        resolved_new_id = _prompt_new_note_id(resolved_reference)
    if not resolved_new_id:
        raise ValueError("Provide a new note ID or keep interactive prompting enabled.")

    note = find_note(index, resolved_reference)
    renamed_path = rename_note(
        workspace,
        reference=resolved_reference,
        new_note_id=resolved_new_id,
        source_path=note.path,
        index=index,
    )
    logger.info("Renamed note to %s", renamed_path.relative_to(workspace.root))
    return 0


def _prompt_new_note_id(reference: str) -> str | None:
    """Prompt for the replacement note ID via questionary."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    return questionary.text("New note ID:").ask()
