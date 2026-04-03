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
        body="\\section{Alpha}\nSee \\nvlink{beta}.",
        links=[Link(target="beta")],
    )
    beta = Note(
        path=tmp_path / "notes" / "proof" / "beta.tex",
        metadata=NoteMetadata(
            id="beta",
            title="Beta",
            note_type="proof",
            created="2026-04-03T00:00:00Z",
            updated="2026-04-03T00:00:00Z",
        ),
        body="\\section{Beta}",
        links=[],
    )

    rendered = render_stitched_document(
        workspace,
        [alpha, beta],
        title="Bundle",
        notes_by_id={"alpha": alpha, "beta": beta},
        aliases={},
    )

    assert r"\usepackage{../tex/novellum}" in rendered
    assert r"\usepackage[numbers]{natbib}" in rendered
    assert r"\title{Bundle}" in rendered
    assert r"\bibliographystyle{plainnat}" in rendered
    assert r"\bibliography{../bibliography/references}" in rendered
    assert r"\label{nv:note:alpha}" in rendered
    assert r"\label{nv:note:beta}" in rendered
    assert r"\hyperref[nv:note:beta]{\texttt{beta}}" in rendered


def test_render_stitched_document_keeps_nonincluded_links_as_nvlink(tmp_path: Path) -> None:
    """Links to notes outside the stitched set should remain as ``\\nvlink``."""

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
        body="\\section{Alpha}\nSee \\nvlink[Outside]{beta}.",
        links=[Link(target="beta", label="Outside")],
    )
    beta = Note(
        path=tmp_path / "notes" / "proof" / "beta.tex",
        metadata=NoteMetadata(
            id="beta",
            title="Beta",
            note_type="proof",
            created="2026-04-03T00:00:00Z",
            updated="2026-04-03T00:00:00Z",
        ),
        body="\\section{Beta}",
        links=[],
    )

    rendered = render_stitched_document(
        workspace,
        [alpha],
        title="Bundle",
        notes_by_id={"alpha": alpha, "beta": beta},
        aliases={},
    )

    assert r"\nvlink[Outside]{beta}" in rendered
