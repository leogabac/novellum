"""Implementation of the ``novellum tag`` command."""

from __future__ import annotations

from pathlib import Path

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.selection import select_note_reference
from novellum.storage import add_tag_note, find_workspace, remove_tag_note


def tag_add_command(
    reference: str | None = None,
    tag: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Add a tag to a note."""

    logger = get_cli_logger("novellum.tag")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    resolved_tag = tag
    if resolved_tag is None and interactive:
        resolved_tag = _prompt_tag("Tag to add:")
    if not resolved_tag:
        raise ValueError("Provide a tag value or keep interactive prompting enabled.")

    note = find_note(index, resolved_reference)
    updated_path = add_tag_note(
        workspace,
        reference=resolved_reference,
        tag=resolved_tag,
        source_path=note.path,
        index=index,
    )
    logger.info(
        "Added tag %s on %s (%s) at %s",
        resolved_tag,
        note.metadata.id,
        note.metadata.title,
        updated_path.relative_to(workspace.root),
    )
    return 0


def tag_remove_command(
    reference: str | None = None,
    tag: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Remove a tag from a note."""

    logger = get_cli_logger("novellum.tag")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    note = find_note(index, resolved_reference)
    resolved_tag = tag
    if resolved_tag is None and interactive:
        resolved_tag = _prompt_tag_to_remove(note.metadata.tags)
    if not resolved_tag:
        raise ValueError("Provide a tag value or keep interactive prompting enabled.")

    updated_path = remove_tag_note(
        workspace,
        reference=resolved_reference,
        tag=resolved_tag,
        source_path=note.path,
        index=index,
    )
    logger.info(
        "Removed tag %s on %s (%s) at %s",
        resolved_tag,
        note.metadata.id,
        note.metadata.title,
        updated_path.relative_to(workspace.root),
    )
    return 0


def _prompt_tag(message: str) -> str | None:
    """Prompt for a tag string."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    return questionary.text(message).ask()


def _prompt_tag_to_remove(tags: list[str]) -> str | None:
    """Prompt the user to choose an existing tag to remove."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    if not tags:
        raise ValueError("The selected note has no tags to remove.")
    return questionary.select("Tag to remove:", choices=tags).ask()
