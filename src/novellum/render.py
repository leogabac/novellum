"""Rendering helpers for stitched LaTeX output."""

from __future__ import annotations

import os
from pathlib import Path

from novellum.models import Note, Workspace


def render_stitched_document(
    workspace: Workspace,
    notes: list[Note],
    output_path: Path | None = None,
    title: str = "Novellum Stitch",
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

    Returns
    -------
    str
        Complete LaTeX document text.
    """

    resolved_output = output_path or (workspace.build_dir / "stitched.tex")
    base_dir = resolved_output.parent
    bibliography_path = _relative_from_base(base_dir, workspace.bibliography_dir / "references.bib")
    package_path = _relative_from_base(base_dir, workspace.tex_dir / "novellum")
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
        note_path = _relative_from_base(base_dir, note.path)
        lines.append(rf"\input{{{note_path}}}")

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

    Returns
    -------
    Path
        Path to the generated document.
    """

    workspace.build_dir.mkdir(parents=True, exist_ok=True)
    destination = output_path or (workspace.build_dir / "stitched.tex")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        render_stitched_document(workspace, notes, output_path=destination, title=title),
        encoding="utf-8",
    )
    return destination


def _relative_from_base(base_dir: Path, target: Path) -> str:
    """Compute a POSIX path from a base directory to a target file."""

    return Path(os.path.relpath(target, start=base_dir)).as_posix()


def _strip_bib_extension(path: str) -> str:
    """Render a bibliography path in BibTeX form without the ``.bib`` suffix."""

    return path[:-4] if path.endswith(".bib") else path
