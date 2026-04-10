"""Implementation of the ``novellum alias`` command."""

from __future__ import annotations

from pathlib import Path

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.selection import select_note_reference
from novellum.storage import add_alias_note, find_workspace, remove_alias_note


def alias_add_command(
    reference: str | None = None,
    alias: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Add an alias to a note."""

    logger = get_cli_logger("novellum.alias")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    resolved_alias = alias
    if resolved_alias is None and interactive:
        resolved_alias = _prompt_alias("Alias to add:")
    if not resolved_alias:
        raise ValueError("Provide an alias value or keep interactive prompting enabled.")

    note = find_note(index, resolved_reference)
    updated_path = add_alias_note(
        workspace,
        reference=resolved_reference,
        alias=resolved_alias,
        source_path=note.path,
        index=index,
    )
    logger.info(
        "Added alias %s on %s (%s) at %s",
        resolved_alias,
        note.metadata.id,
        note.metadata.title,
        updated_path.relative_to(workspace.root),
    )
    return 0


def alias_remove_command(
    reference: str | None = None,
    alias: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Remove an alias from a note."""

    logger = get_cli_logger("novellum.alias")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    note = find_note(index, resolved_reference)
    resolved_alias = alias
    if resolved_alias is None and interactive:
        resolved_alias = _prompt_alias_to_remove(note.metadata.aliases)
    if not resolved_alias:
        raise ValueError("Provide an alias value or keep interactive prompting enabled.")

    updated_path = remove_alias_note(
        workspace,
        reference=resolved_reference,
        alias=resolved_alias,
        source_path=note.path,
        index=index,
    )
    logger.info(
        "Removed alias %s on %s (%s) at %s",
        resolved_alias,
        note.metadata.id,
        note.metadata.title,
        updated_path.relative_to(workspace.root),
    )
    return 0


def _prompt_alias(message: str) -> str | None:
    """Prompt for an alias string."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    return questionary.text(message).ask()


def _prompt_alias_to_remove(aliases: list[str]) -> str | None:
    """Prompt the user to choose an existing alias to remove."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    if not aliases:
        raise ValueError("The selected note has no aliases to remove.")
    return questionary.select("Alias to remove:", choices=aliases).ask()
