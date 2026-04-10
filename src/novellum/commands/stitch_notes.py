"""Implementation of the ``novellum stitch`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.render import write_stitched_document
from novellum.selection import select_note_references
from novellum.storage import find_workspace, list_notes


def stitch_command(
    references: list[str],
    stitch_all: bool = False,
    note_types: list[str] | None = None,
    interactive: bool = True,
    title: str = "Novellum Stitch",
    output_path: Path | None = None,
    cwd: Path = Path("."),
) -> int:
    """Generate a stitched LaTeX document from selected notes.

    Parameters
    ----------
    references : list[str]
        Note IDs or aliases to include, in the requested order.
    stitch_all : bool, optional
        When true, stitch every note in the workspace using filesystem sort
        order instead of explicit references.
    note_types : list[str] or None, optional
        Include every note from the selected categories using filesystem sort
        order. Can be combined with explicit references.
    interactive : bool, optional
        Whether interactive note selection should be attempted when explicit
        references are omitted.
    title : str, optional
        Document title for the generated output.
    output_path : Path or None, optional
        Explicit output path. Defaults to ``build/stitched.tex``.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    selected_types = note_types or []
    if stitch_all:
        if references or selected_types:
            raise ValueError("Use either explicit note references/category flags or --all, not both.")
        notes = list_notes(workspace)
    else:
        notes = [find_note(index, reference) for reference in references]
        selected_ids = {note.metadata.id for note in notes}
        for note_type in selected_types:
            for note in list_notes(workspace, note_type=note_type):
                if note.metadata.id in selected_ids:
                    continue
                notes.append(note)
                selected_ids.add(note.metadata.id)

        if not notes and interactive:
            selected_references = select_note_references(index) or []
            notes = [find_note(index, reference) for reference in selected_references]
        if not notes:
            raise ValueError(
                "Provide note references, pass category flags, use --all, or install fzf for interactive selection."
            )

    resolved_output = output_path
    if resolved_output is not None and not resolved_output.is_absolute():
        resolved_output = workspace.root / resolved_output

    stitched_path = write_stitched_document(
        workspace,
        notes,
        output_path=resolved_output,
        title=title,
        notes_by_id=index.notes_by_id,
        aliases=index.aliases,
    )
    print(f"Wrote stitched document to {stitched_path.relative_to(workspace.root)}")
    return 0
