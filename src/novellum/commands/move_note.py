"""Implementation of the ``novellum move`` command."""

from __future__ import annotations

from pathlib import Path

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.selection import select_note_reference
from novellum.storage import find_workspace, get_note_types, move_note


def move_command(
    reference: str | None = None,
    new_note_type: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Move a note into another note-type directory."""

    logger = get_cli_logger("novellum.move")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    note = find_note(index, resolved_reference)
    resolved_new_type = new_note_type
    if resolved_new_type is None and interactive:
        resolved_new_type = _prompt_new_note_type(note.metadata.note_type, get_note_types(workspace))
    if not resolved_new_type:
        raise ValueError("Provide a destination note type or keep interactive prompting enabled.")

    moved_path = move_note(
        workspace,
        reference=resolved_reference,
        new_note_type=resolved_new_type,
        source_path=note.path,
    )
    logger.info("Moved note to %s", moved_path.relative_to(workspace.root))
    return 0


def _prompt_new_note_type(current_note_type: str, note_types: tuple[str, ...]) -> str | None:
    """Prompt for the destination note type via questionary."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    choices = [note_type for note_type in note_types if note_type != current_note_type]
    return questionary.select("Destination note type:", choices=choices).ask()
