"""Tests for stitched LaTeX rendering."""

from pathlib import Path

from novellum.models import Link, Note, NoteMetadata
from novellum.render import render_stitched_document
from novellum.storage import init_workspace


def test_render_stitched_document_uses_build_relative_paths(tmp_path: Path) -> None:
    """Rendered stitched output should reference workspace assets from build/."""

    workspace = init_workspace(tmp_path)
    alpha = Note(
        path=tmp_path / "notes" / "concept" / "alpha.tex",
        metadata=NoteMetadata(
            id="alpha",
            title="Alpha",
            note_type="concept",
            created="2026-04-03T00:00:00Z",
            updated="2026-04-03T00:00:00Z",
        ),
        body="\\section{Alpha}",
        links=[Link(target="beta")],
    )

    rendered = render_stitched_document(workspace, [alpha], title="Bundle")

    assert r"\usepackage{../tex/novellum}" in rendered
    assert r"\addbibresource{../bibliography/references.bib}" in rendered
    assert r"\title{Bundle}" in rendered
    assert r"\input{../notes/concept/alpha.tex}" in rendered
