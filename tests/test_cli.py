"""CLI-level tests for the current command surface."""

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import subprocess

from novellum.cli import main


def test_init_command_creates_workspace(tmp_path: Path) -> None:
    """``novellum init`` should create the workspace marker and config."""

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["init", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / ".novellum" / "config.toml").exists()


def test_new_and_list_commands_work_in_workspace(tmp_path: Path) -> None:
    """``new`` and ``list`` should create and display notes."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    new_output = io.StringIO()
    list_output = io.StringIO()
    with redirect_stdout(new_output):
        new_exit_code = main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])
    with redirect_stdout(list_output):
        list_exit_code = main(["list", "--cwd", str(tmp_path)])

    assert new_exit_code == 0
    assert list_exit_code == 0
    assert "spectral-gap" in list_output.getvalue()


def test_show_links_and_search_commands_work(tmp_path: Path) -> None:
    """Navigation commands should work against a small hand-written graph."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    note_one = """% novellum:begin
% id: alpha
% title: Alpha Note
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: first
% novellum:end

\\section{Alpha}
See \\nvlink{beta}.
"""
    note_two = """% novellum:begin
% id: beta
% title: Beta Note
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
Mentions Poincare.
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(note_one, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(note_two, encoding="utf-8")

    show_output = io.StringIO()
    links_output = io.StringIO()
    search_output = io.StringIO()

    with redirect_stdout(show_output):
        show_exit_code = main(["show", "alpha", "--cwd", str(tmp_path)])
    with redirect_stdout(links_output):
        links_exit_code = main(["links", "beta", "--cwd", str(tmp_path)])
    with redirect_stdout(search_output):
        search_exit_code = main(["search", "poincare", "--cwd", str(tmp_path)])

    assert show_exit_code == 0
    assert links_exit_code == 0
    assert search_exit_code == 0
    assert "Alpha Note" in show_output.getvalue()
    assert "Backlinks:" in links_output.getvalue()
    assert "alpha -> beta" in links_output.getvalue()
    assert "beta" in search_output.getvalue()


def test_backlinks_and_broken_commands_work(tmp_path: Path) -> None:
    """Dedicated diagnostics commands should expose inbound and broken links."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    alpha = """% novellum:begin
% id: alpha
% title: Alpha Note
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
See \\nvlink{beta}, \\nvlink{missing}, and \\nvlink{shared}.
"""
    beta = """% novellum:begin
% id: beta
% title: Beta Note
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
See \\nvlink[Alpha Ref]{alpha}.
"""
    gamma = """% novellum:begin
% id: gamma
% title: Gamma Note
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: shared
% novellum:end

\\section{Gamma}
"""
    delta = """% novellum:begin
% id: delta
% title: Delta Note
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: shared
% novellum:end

\\section{Delta}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")
    (tmp_path / "notes" / "concept" / "gamma.tex").write_text(gamma, encoding="utf-8")
    (tmp_path / "notes" / "concept" / "delta.tex").write_text(delta, encoding="utf-8")

    backlinks_output = io.StringIO()
    broken_output = io.StringIO()

    with redirect_stdout(backlinks_output):
        backlinks_exit_code = main(["backlinks", "alpha", "--cwd", str(tmp_path)])
    with redirect_stdout(broken_output):
        broken_exit_code = main(["broken", "--cwd", str(tmp_path)])

    assert backlinks_exit_code == 0
    assert broken_exit_code == 0
    assert "beta -> alpha [Alpha Ref]" in backlinks_output.getvalue()
    assert "- missing [missing]" in broken_output.getvalue()
    assert "- shared [ambiguous: delta, gamma]" in broken_output.getvalue()


def test_edit_command_opens_note_with_editor(tmp_path: Path, monkeypatch) -> None:
    """``edit`` should resolve a note and invoke the configured editor."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--cwd", str(tmp_path)])

    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        captured["command"] = command
        captured["check"] = check
        captured["cwd"] = cwd

    monkeypatch.setenv("EDITOR", "vim -f")
    monkeypatch.setattr(subprocess, "run", fake_run)

    exit_code = main(["edit", "spectral-gap", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert captured["command"] == ["vim", "-f", str(tmp_path / "notes" / "concept" / "spectral-gap.tex")]
    assert captured["check"] is True
    assert captured["cwd"] == tmp_path


def test_edit_command_requires_editor(tmp_path: Path, monkeypatch) -> None:
    """``edit`` should fail clearly when ``$EDITOR`` is missing."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--cwd", str(tmp_path)])

    monkeypatch.delenv("EDITOR", raising=False)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["edit", "spectral-gap", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "$EDITOR" in error_output.getvalue()


def test_show_reports_missing_note_as_cli_error(tmp_path: Path) -> None:
    """Lookup failures should produce CLI-style stderr output."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["show", "does-not-exist", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "No note found" in error_output.getvalue()


def test_show_reports_ambiguous_alias_as_cli_error(tmp_path: Path) -> None:
    """Ambiguous aliases should be reported as user-facing CLI errors."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: shared
% novellum:end

\\section{Alpha}
"""
    beta = """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: shared
% novellum:end

\\section{Beta}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["show", "shared", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "ambiguous" in error_output.getvalue()


def test_show_reports_duplicate_ids_as_cli_error(tmp_path: Path) -> None:
    """Duplicate IDs should surface as a CLI error on index-backed commands."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    duplicate_one = """% novellum:begin
% id: duplicate
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
"""
    duplicate_two = """% novellum:begin
% id: duplicate
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(duplicate_one, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(duplicate_two, encoding="utf-8")

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["show", "duplicate", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Duplicate note ID" in error_output.getvalue()
