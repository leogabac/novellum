"""Implementation of the ``novellum stitch`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.render import write_stitched_document
from novellum.storage import find_workspace, list_notes


def stitch_command(
    references: list[str],
    stitch_all: bool = False,
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
    if stitch_all:
        if references:
            raise ValueError("Use either explicit note references or --all, not both.")
        notes = list_notes(workspace)
    else:
        if not references:
            raise ValueError("Provide at least one note reference or pass --all.")
        index = load_index(workspace)
        notes = [find_note(index, reference) for reference in references]

    resolved_output = output_path
    if resolved_output is not None and not resolved_output.is_absolute():
        resolved_output = workspace.root / resolved_output

    stitched_path = write_stitched_document(
        workspace,
        notes,
        output_path=resolved_output,
        title=title,
    )
    print(f"Wrote stitched document to {stitched_path.relative_to(workspace.root)}")
    return 0
