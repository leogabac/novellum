"""Implementation of the ``novellum rename`` command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

try:
    import questionary
except ImportError:  # pragma: no cover
    questionary = None

from novellum.index import find_note, load_index
from novellum.logging import get_cli_logger
from novellum.parser import preview_link_target_rewrites
from novellum.selection import select_note_reference
from novellum.storage import find_workspace, rename_note

if TYPE_CHECKING:
    from logging import Logger

    from novellum.index import NoteIndex
    from novellum.models import Note, Workspace


def rename_command(
    reference: str | None = None,
    new_note_id: str | None = None,
    rewrite_links: bool = True,
    dry_run: bool = False,
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
    if dry_run:
        _preview_rename(
            workspace=workspace,
            index=index,
            note=note,
            new_note_id=resolved_new_id,
            rewrite_links=rewrite_links,
            logger=logger,
        )
        return 0

    renamed_path = rename_note(
        workspace,
        reference=resolved_reference,
        new_note_id=resolved_new_id,
        rewrite_links=rewrite_links,
        source_path=note.path,
        index=index,
    )
    if rewrite_links:
        logger.info(
            "Renamed note to %s and rewrote inbound links",
            renamed_path.relative_to(workspace.root),
        )
    else:
        logger.info("Renamed note to %s", renamed_path.relative_to(workspace.root))
    return 0


def _prompt_new_note_id(reference: str) -> str | None:
    """Prompt for the replacement note ID via questionary."""

    if questionary is None:
        raise RuntimeError("questionary is not installed or not available in this environment.")
    return questionary.text("New note ID:").ask()


def _preview_rename(
    *,
    workspace: Workspace,
    index: NoteIndex,
    note: Note,
    new_note_id: str,
    rewrite_links: bool,
    logger: Logger,
) -> None:
    """Log a dry-run preview for rename."""

    destination = note.path.with_name(f"{new_note_id}.tex")
    logger.info(
        "Dry run: would rename %s to %s",
        note.path.relative_to(workspace.root),
        destination.relative_to(workspace.root),
    )
    if not rewrite_links:
        logger.info("Dry run: inbound link rewriting disabled")
        return

    backlink_paths = sorted(
        {
            index.notes_by_id[link.source_id].path
            for link in index.backlinks.get(note.metadata.id, [])
            if link.source_id in index.notes_by_id
        },
        key=str,
    )
    previews: list[tuple[Path, list[tuple[int, str, str]]]] = []
    for path in backlink_paths:
        matches = preview_link_target_rewrites(path.read_text(encoding="utf-8"), note.metadata.id, new_note_id)
        if not matches:
            continue
        previews.append(
            (
                path.relative_to(workspace.root),
                [(match.line_number, match.original, match.replacement) for match in matches],
            )
        )

    if not previews:
        logger.info("Dry run: no inbound links would be rewritten")
        return

    rewrite_count = sum(len(matches) for _, matches in previews)
    logger.info(
        "Dry run: would rewrite %d inbound link(s) across %d note(s)",
        rewrite_count,
        len(previews),
    )
    for path, matches in previews:
        logger.info("  %s", path)
        for line_number, original, replacement in matches:
            logger.info("    L%d: %s -> %s", line_number, original, replacement)
