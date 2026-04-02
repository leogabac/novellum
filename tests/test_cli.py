from pathlib import Path
import io
from contextlib import redirect_stdout

from novellum.cli import main


def test_init_command_creates_workspace(tmp_path: Path) -> None:
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["init", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / ".novellum" / "config.toml").exists()


def test_new_and_list_commands_work_in_workspace(tmp_path: Path) -> None:
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
