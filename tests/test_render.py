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

    assert rendered.index(r"\documentclass{article}") < rendered.index(r"\input{../tex/stitched-preamble.tex}")
    assert r"\usepackage{amsmath,amssymb,amsthm}" not in rendered
    assert r"\usepackage{../tex/novellum}" in rendered
    assert r"\usepackage[numbers]{natbib}" in rendered
    assert r"\input{../tex/stitched-preamble.tex}" in rendered
    assert r"\title{Bundle}" in rendered
    assert r"\bibliographystyle{plainnat}" in rendered
    assert r"\bibliography{../bibliography/references}" in rendered
    assert r"\label{nv:note:alpha}" in rendered
    assert r"\label{nv:note:beta}" in rendered
    assert r"\nvstitchlink{nv:note:beta}{beta}" in rendered


def test_render_stitched_document_skips_missing_custom_preamble(tmp_path: Path) -> None:
    """Rendered stitched output should not reference a deleted preamble file."""

    workspace = init_workspace(tmp_path)
    (workspace.tex_dir / "stitched-preamble.tex").unlink()
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
        links=[],
    )

    rendered = render_stitched_document(workspace, [alpha], title="Bundle", notes_by_id={"alpha": alpha}, aliases={})

    assert r"\input{../tex/stitched-preamble.tex}" not in rendered


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


def test_render_stitched_document_marks_labeled_internal_links(tmp_path: Path) -> None:
    """Included labeled links should use the stitched label treatment."""

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
        [alpha, beta],
        title="Bundle",
        notes_by_id={"alpha": alpha, "beta": beta},
        aliases={},
    )

    assert r"\nvstitchlabel{nv:note:beta}{Outside}" in rendered


def test_render_stitched_document_provides_fallback_stitch_macros(tmp_path: Path) -> None:
    """Stitched output should compile even if the workspace style file is older."""

    workspace = init_workspace(tmp_path)
    legacy_style = r"""\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{novellum}[2026/04/03 Novellum note helpers]

\RequirePackage{xparse}
\RequirePackage{hyperref}

\NewDocumentCommand{\nvlink}{O{} m}{%
  \IfNoValueTF{#1}{%
    \texttt{#2}%
  }{%
    #1%
  }%
}
"""
    (workspace.tex_dir / "novellum.sty").write_text(legacy_style, encoding="utf-8")
    alpha = Note(
        path=tmp_path / "notes" / "concept" / "alpha.tex",
        metadata=NoteMetadata(
            id="alpha",
            title="Alpha",
            note_type="concept",
            created="2026-04-03T00:00:00Z",
            updated="2026-04-03T00:00:00Z",
        ),
        body="\\section{Alpha}\nSee \\nvlink{beta} and \\nvlink[Outside]{beta}.",
        links=[Link(target="beta"), Link(target="beta", label="Outside")],
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

    assert r"\providecommand{\nvstitchlink}[2]{\hyperref[#1]{\texttt{#2}}}" in rendered
    assert r"\providecommand{\nvstitchlabel}[2]{\hyperref[#1]{#2\,\textsf{[note]}}}" in rendered
