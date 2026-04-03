"""Rendering helpers for stitched LaTeX output."""

from __future__ import annotations

import os
from pathlib import Path

from novellum.models import Note, Workspace
from novellum.parser import LINK_PATTERN


def render_stitched_document(
    workspace: Workspace,
    notes: list[Note],
    output_path: Path | None = None,
    title: str = "Novellum Stitch",
    notes_by_id: dict[str, Note] | None = None,
    aliases: dict[str, list[str]] | None = None,
) -> str:
    """Render a standalone LaTeX document that inputs selected notes.

    Parameters
    ----------
    workspace : Workspace
        Workspace providing bibliography and helper package paths.
    notes : list[Note]
        Notes to include, in the exact order they should appear.
    output_path : Path or None, optional
        Output file location used to compute relative asset paths. Defaults to
        ``build/stitched.tex``.
    title : str, optional
        Document title for the stitched output.
    notes_by_id : dict[str, Note] or None, optional
        Global note lookup used to resolve stitched hyperlinks.
    aliases : dict[str, list[str]] or None, optional
        Global alias lookup used to resolve stitched hyperlinks.

    Returns
    -------
    str
        Complete LaTeX document text.
    """

    resolved_output = output_path or (workspace.build_dir / "stitched.tex")
    base_dir = resolved_output.parent
    bibliography_path = _relative_from_base(base_dir, workspace.bibliography_dir / "references.bib")
    package_path = _relative_from_base(base_dir, workspace.tex_dir / "novellum")
    resolved_notes_by_id = notes_by_id or {note.metadata.id: note for note in notes}
    resolved_aliases = aliases or _build_aliases(notes)
    included_ids = {note.metadata.id for note in notes}
    lines = [
        r"\documentclass{article}",
        "",
        r"\usepackage{amsmath,amssymb,amsthm}",
        rf"\usepackage{{{package_path}}}",
        r"\usepackage[numbers]{natbib}",
        "",
        rf"\title{{{title}}}",
        r"\author{}",
        r"\date{\today}",
        "",
        r"\begin{document}",
        "",
        r"\maketitle",
        r"\tableofcontents",
        "",
    ]

    for note in notes:
        lines.extend(
            [
                f"% note: {note.metadata.id}",
                r"\phantomsection",
                rf"\label{{{_note_anchor(note.metadata.id)}}}",
                _render_note_body(
                    note,
                    included_ids=included_ids,
                    notes_by_id=resolved_notes_by_id,
                    aliases=resolved_aliases,
                ).rstrip(),
                "",
            ]
        )

    lines.extend(
        [
            "",
            r"\bibliographystyle{plainnat}",
            rf"\bibliography{{{_strip_bib_extension(bibliography_path)}}}",
            "",
            r"\end{document}",
            "",
        ]
    )
    return "\n".join(lines)


def write_stitched_document(
    workspace: Workspace,
    notes: list[Note],
    output_path: Path | None = None,
    title: str = "Novellum Stitch",
    notes_by_id: dict[str, Note] | None = None,
    aliases: dict[str, list[str]] | None = None,
) -> Path:
    """Write a stitched LaTeX document to the workspace build directory.

    Parameters
    ----------
    workspace : Workspace
        Workspace owning the build directory.
    notes : list[Note]
        Notes to include, in the exact order they should appear.
    output_path : Path or None, optional
        Explicit output path. Defaults to ``build/stitched.tex``.
    title : str, optional
        Document title for the stitched output.
    notes_by_id : dict[str, Note] or None, optional
        Global note lookup used to resolve stitched hyperlinks.
    aliases : dict[str, list[str]] or None, optional
        Global alias lookup used to resolve stitched hyperlinks.

    Returns
    -------
    Path
        Path to the generated document.
    """

    workspace.build_dir.mkdir(parents=True, exist_ok=True)
    destination = output_path or (workspace.build_dir / "stitched.tex")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_stitched_document(
            workspace,
            notes,
            output_path=destination,
            title=title,
            notes_by_id=notes_by_id,
            aliases=aliases,
        ),
        encoding="utf-8",
    )
    return destination


def _relative_from_base(base_dir: Path, target: Path) -> str:
    """Compute a POSIX path from a base directory to a target file."""

    return Path(os.path.relpath(target, start=base_dir)).as_posix()


def _strip_bib_extension(path: str) -> str:
    """Render a bibliography path in BibTeX form without the ``.bib`` suffix."""

    return path[:-4] if path.endswith(".bib") else path


def _render_note_body(
    note: Note,
    included_ids: set[str],
    notes_by_id: dict[str, Note],
    aliases: dict[str, list[str]],
) -> str:
    """Rewrite internal links to clickable stitched-document hyperlinks."""

    def replace_link(match) -> str:
        target = match.group("target").strip()
        label = match.group("label")
        resolved = _resolve_reference(target, notes_by_id, aliases)
        if resolved is None or resolved not in included_ids:
            return match.group(0)

        display = label if label is not None else rf"\texttt{{{target}}}"
        return rf"\hyperref[{_note_anchor(resolved)}]{{{display}}}"

    return LINK_PATTERN.sub(replace_link, note.body)


def _resolve_reference(
    reference: str,
    notes_by_id: dict[str, Note],
    aliases: dict[str, list[str]],
) -> str | None:
    """Resolve a reference only when it maps uniquely to one note."""

    if reference in notes_by_id:
        return reference
    matches = sorted(set(aliases.get(reference, [])))
    if len(matches) != 1:
        return None
    return matches[0]


def _build_aliases(notes: list[Note]) -> dict[str, list[str]]:
    """Build a minimal alias map for stitched rendering."""

    aliases: dict[str, list[str]] = {}
    for note in notes:
        for alias in note.metadata.aliases:
            aliases.setdefault(alias, []).append(note.metadata.id)
    return aliases


def _note_anchor(note_id: str) -> str:
    """Return the LaTeX anchor label for a stitched note."""

    return f"nv:note:{note_id}"
