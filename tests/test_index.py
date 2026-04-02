from pathlib import Path

from novellum.index import build_index, find_note, search_notes
from novellum.storage import init_workspace


def write_note(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_index_builds_backlinks_and_broken_links(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)
    write_note(
        tmp_path / "notes" / "concept" / "alpha.tex",
        """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: first
% novellum:end

\\section{Alpha}
See \\nvlink{beta} and \\nvlink{missing}.
""",
    )
    write_note(
        tmp_path / "notes" / "proof" / "beta.tex",
        """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: second, first
% novellum:end

\\section{Beta}
See \\nvlink{alpha}.
""",
    )

    index = build_index(workspace)

    assert [link.resolved_id for link in index.outbound["alpha"]] == ["beta", None]
    assert [link.source_id for link in index.backlinks["alpha"]] == ["beta"]
    assert [link.target for link in index.broken_links["alpha"]] == ["missing"]


def test_find_note_resolves_ids_and_reports_ambiguous_aliases(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)
    write_note(
        tmp_path / "notes" / "concept" / "alpha.tex",
        """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: first
% novellum:end

\\section{Alpha}
""",
    )
    write_note(
        tmp_path / "notes" / "proof" / "beta.tex",
        """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: first
% novellum:end

\\section{Beta}
""",
    )

    index = build_index(workspace)

    assert find_note(index, "alpha").metadata.id == "alpha"
    try:
        find_note(index, "first")
    except LookupError as error:
        assert "ambiguous" in str(error)
    else:
        raise AssertionError("Expected ambiguous alias resolution to fail.")


def test_search_notes_matches_metadata_and_body(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)
    write_note(
        tmp_path / "notes" / "concept" / "alpha.tex",
        """% novellum:begin
% id: alpha
% title: Spectral Gap
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% tags: analysis
% aliases: sg
% novellum:end

\\section{Spectral Gap}
Poincare inequality.
""",
    )

    index = build_index(workspace)

    assert [note.metadata.id for note in search_notes(index, "spectral")] == ["alpha"]
    assert [note.metadata.id for note in search_notes(index, "analysis")] == ["alpha"]
    assert [note.metadata.id for note in search_notes(index, "sg")] == ["alpha"]
    assert [note.metadata.id for note in search_notes(index, "poincare")] == ["alpha"]
