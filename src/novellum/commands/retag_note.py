"""Implementation of the ``novellum retag`` command."""

from __future__ import annotations

from pathlib import Path

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.selection import select_note_reference
from novellum.storage import find_workspace, retag_note


def retag_command(
    reference: str | None = None,
    tags: list[str] | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Replace a note's tag list."""

    logger = get_cli_logger("novellum.retag")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")

    resolved_tags = tags
    if not resolved_tags and interactive:
        resolved_tags = _prompt_tags()
    if resolved_tags is None:
        raise ValueError("Provide at least one --tag value or keep interactive prompting enabled.")

    note = find_note(index, resolved_reference)
    updated_path = retag_note(
        workspace,
        reference=resolved_reference,
        tags=resolved_tags,
        source_path=note.path,
        index=index,
    )
    logger.info("Retagged note %s", updated_path.relative_to(workspace.root))
    return 0


def _prompt_tags() -> list[str] | None:
    """Prompt for a comma-separated replacement tag list."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    response = questionary.text("Tags (comma-separated, blank for none):").ask()
    if response is None:
        return None
    return [part.strip() for part in response.split(",") if part.strip()]
