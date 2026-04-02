from pathlib import Path

from novellum.parser import extract_links, parse_note_text


def test_parse_note_text_reads_comment_metadata_block() -> None:
    text = """% novellum:begin
% id: spectral-gap
% title: Spectral Gap
% type: concept
% created: 2026-04-02T00:00:00Z
% updated: 2026-04-02T00:00:00Z
% tags: analysis, operator-theory
% aliases: sg
% novellum:end

\\section{Spectral Gap}
See \\nvlink[The Poincare Lemma]{lemma-poincare}.
"""
    note = parse_note_text(text, Path("spectral-gap.tex"))

    assert note.metadata.id == "spectral-gap"
    assert note.metadata.note_type == "concept"
    assert note.metadata.tags == ["analysis", "operator-theory"]
    assert note.links[0].target == "lemma-poincare"
    assert note.links[0].label == "The Poincare Lemma"


def test_extract_links_parses_latex_native_link_commands() -> None:
    body = r"\nvlink{a-note} and \nvlink[Displayed]{other-note}"

    links = extract_links(body)

    assert [link.target for link in links] == ["a-note", "other-note"]
    assert [link.label for link in links] == [None, "Displayed"]


def test_extract_links_ignores_commented_link_examples() -> None:
    body = "% \\nvlink{commented}\n\\nvlink{live-link}\n"

    links = extract_links(body)

    assert [link.target for link in links] == ["live-link"]
