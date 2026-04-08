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


def test_log_new_creates_dated_log_note(tmp_path: Path) -> None:
    """``log new`` should create a log note with a stable date-based ID."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["log", "new", "--date", "2026-04-03", "--cwd", str(tmp_path)])

    note_path = tmp_path / "notes" / "log" / "log-2026-04-03.tex"
    note_text = note_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert note_path.exists()
    assert "Created log note notes/log/log-2026-04-03.tex" in output.getvalue()
    assert "% id: log-2026-04-03" in note_text
    assert "% type: log" in note_text
    assert "% tags: log, 2026-04-03" in note_text
    assert "\\section*{Research Log: 2026-04-03}" in note_text


def test_log_new_reports_existing_log_note(tmp_path: Path) -> None:
    """``log new`` should be idempotent for an existing date-based log note."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["log", "new", "--date", "2026-04-03", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["log", "new", "--date", "2026-04-03", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert "Log note already exists" in output.getvalue()


def test_today_creates_and_opens_todays_log_note(tmp_path: Path, monkeypatch) -> None:
    """``today`` should create today's log note when missing and open it."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        captured["command"] = command
        captured["check"] = check
        captured["cwd"] = cwd

    monkeypatch.setenv("EDITOR", "vim -f")
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["today", "--cwd", str(tmp_path)])

    from datetime import date

    today_value = date.today().isoformat()
    note_path = tmp_path / "notes" / "log" / f"log-{today_value}.tex"
    assert exit_code == 0
    assert note_path.exists()
    assert f"Created log note notes/log/log-{today_value}.tex" in output.getvalue()
    assert captured["command"] == ["vim", "-f", str(note_path)]
    assert captured["check"] is True
    assert captured["cwd"] == tmp_path


def test_today_opens_existing_log_note_without_recreating(tmp_path: Path, monkeypatch) -> None:
    """``today`` should open the current day's note if it already exists."""

    from datetime import date

    today_value = date.today().isoformat()
    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["log", "new", "--date", today_value, "--cwd", str(tmp_path)])

    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        captured["command"] = command
        captured["check"] = check
        captured["cwd"] = cwd

    monkeypatch.setenv("EDITOR", "vim -f")
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["today", "--cwd", str(tmp_path)])

    note_path = tmp_path / "notes" / "log" / f"log-{today_value}.tex"
    assert exit_code == 0
    assert "Created log note" not in output.getvalue()
    assert captured["command"] == ["vim", "-f", str(note_path)]


def test_log_new_requires_valid_iso_date(tmp_path: Path) -> None:
    """``log new`` should reject invalid date strings with a CLI error."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["log", "new", "--date", "04-03-2026", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Log date must use YYYY-MM-DD format." in error_output.getvalue()


def test_stitch_command_writes_document_in_requested_order(tmp_path: Path) -> None:
    """``stitch`` should emit a standalone document using explicit note order."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% aliases: first
% novellum:end

\\section{Alpha}
"""
    beta = """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(
            [
                "stitch",
                "beta",
                "first",
                "--title",
                "Demo Bundle",
                "--cwd",
                str(tmp_path),
            ]
        )

    stitched_path = tmp_path / "build" / "stitched.tex"
    stitched_text = stitched_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "build/stitched.tex" in output.getvalue()
    assert r"\title{Demo Bundle}" in stitched_text
    assert stitched_text.index("% note: beta") < stitched_text.index("% note: alpha")


def test_stitch_command_honors_custom_output_path(tmp_path: Path) -> None:
    """``stitch`` should support an explicit output path relative to the workspace."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")

    custom_output = tmp_path / "build" / "drafts" / "alpha.tex"
    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(
            [
                "stitch",
                "alpha",
                "--output",
                "build/drafts/alpha.tex",
                "--cwd",
                str(tmp_path),
            ]
        )

    assert exit_code == 0
    assert custom_output.exists()
    assert "build/drafts/alpha.tex" in output.getvalue()


def test_stitch_command_can_render_whole_workspace(tmp_path: Path) -> None:
    """``stitch --all`` should include every note in deterministic workspace order."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
"""
    beta = """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
"""
    gamma = """% novellum:begin
% id: gamma
% title: Gamma
% type: experiment
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Gamma}
"""
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "experiment" / "gamma.tex").write_text(gamma, encoding="utf-8")

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["stitch", "--all", "--cwd", str(tmp_path)])

    stitched_text = (tmp_path / "build" / "stitched.tex").read_text(encoding="utf-8")

    assert exit_code == 0
    assert stitched_text.index("% note: alpha") < stitched_text.index("% note: gamma")
    assert stitched_text.index("% note: gamma") < stitched_text.index("% note: beta")


def test_stitch_command_requires_references_or_all(tmp_path: Path) -> None:
    """``stitch`` should fail clearly when no note selection is provided."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["stitch", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide note references, pass --all, or install fzf" in error_output.getvalue()


def test_stitch_command_rejects_references_with_all(tmp_path: Path) -> None:
    """``stitch`` should reject mixing explicit references with ``--all``."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["stitch", "alpha", "--all", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Use either explicit note references or --all" in error_output.getvalue()


def test_compile_command_uses_workspace_root_by_default(tmp_path: Path, monkeypatch) -> None:
    """``compile`` should default to the configured workspace root document."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        captured["command"] = command
        captured["check"] = check
        captured["cwd"] = cwd

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/latexmk" if name == "latexmk" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["compile", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert captured["command"] == [
        "/usr/bin/latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-output-directory=build",
        "tex/workspace.tex",
    ]
    assert captured["check"] is True
    assert captured["cwd"] == tmp_path
    assert "Compiled tex/workspace.tex into build" in output.getvalue()


def test_compile_command_can_target_stitched_document(tmp_path: Path, monkeypatch) -> None:
    """``compile stitched`` should compile the default stitched output."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    (tmp_path / "build" / "stitched.tex").write_text("\\documentclass{article}\n", encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        captured["command"] = command
        captured["check"] = check
        captured["cwd"] = cwd

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/latexmk" if name == "latexmk" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    exit_code = main(["compile", "stitched", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert captured["command"] == [
        "/usr/bin/latexmk",
        "-pdf",
        "-interaction=nonstopmode",
        "-output-directory=.",
        "stitched.tex",
    ]
    assert captured["cwd"] == tmp_path / "build"


def test_compile_command_reports_missing_latexmk(tmp_path: Path, monkeypatch) -> None:
    """``compile`` should fail cleanly when ``latexmk`` is unavailable."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    monkeypatch.setattr("shutil.which", lambda name: None)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["compile", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "latexmk is not installed" in error_output.getvalue()


def test_compile_command_reports_missing_target(tmp_path: Path, monkeypatch) -> None:
    """``compile`` should fail cleanly when the requested source file is missing."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/latexmk" if name == "latexmk" else None)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["compile", "build/missing.tex", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Compile target does not exist" in error_output.getvalue()


def test_compile_command_reports_empty_stitched_preamble_helpfully(tmp_path: Path, monkeypatch) -> None:
    """``compile stitched`` should explain the empty-preamble trap cleanly."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    (tmp_path / "build" / "stitched.tex").write_text("\\documentclass{article}\n", encoding="utf-8")
    (tmp_path / "build" / "stitched.log").write_text(
        "! Undefined control sequence.\n"
        "l.51     \\dv{x}{t} = v_t(x).\n",
        encoding="utf-8",
    )

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        raise subprocess.CalledProcessError(returncode=12, cmd=command)

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/latexmk" if name == "latexmk" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["compile", "stitched", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "stitched-preamble.tex only contains comments" in error_output.getvalue()
    assert "\\usepackage{physics}" in error_output.getvalue()


def test_open_command_defaults_to_stitched_pdf(tmp_path: Path, monkeypatch) -> None:
    """``open`` should default to the stitched PDF output."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    (tmp_path / "build" / "stitched.pdf").write_bytes(b"%PDF-1.4\n")

    captured: dict[str, object] = {}

    class DummyProcess:
        pass

    def fake_popen(command: list[str], cwd: Path) -> DummyProcess:
        captured["command"] = command
        captured["cwd"] = cwd
        return DummyProcess()

    monkeypatch.delenv("NOVELLUM_PDF_VIEWER", raising=False)
    monkeypatch.delenv("PDF_VIEWER", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/zathura" if name == "zathura" else None)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["open", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert captured["command"] == ["/usr/bin/zathura", str(tmp_path / "build" / "stitched.pdf")]
    assert captured["cwd"] == tmp_path
    assert "Opened build/stitched.pdf" in output.getvalue()


def test_open_command_honors_configured_pdf_viewer(tmp_path: Path, monkeypatch) -> None:
    """``open`` should use the configured viewer command when provided."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    (tmp_path / "build" / "workspace.pdf").write_bytes(b"%PDF-1.4\n")

    captured: dict[str, object] = {}

    class DummyProcess:
        pass

    def fake_popen(command: list[str], cwd: Path) -> DummyProcess:
        captured["command"] = command
        captured["cwd"] = cwd
        return DummyProcess()

    monkeypatch.setenv("NOVELLUM_PDF_VIEWER", "okular --unique")
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    exit_code = main(["open", "workspace", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert captured["command"] == ["okular", "--unique", str(tmp_path / "build" / "workspace.pdf")]
    assert captured["cwd"] == tmp_path


def test_open_command_reports_missing_pdf(tmp_path: Path) -> None:
    """``open`` should fail clearly when the compiled PDF is missing."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["open", "stitched", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Compiled PDF does not exist" in error_output.getvalue()


def test_open_command_reports_missing_viewer(tmp_path: Path, monkeypatch) -> None:
    """``open`` should fail clearly when no viewer is available."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    (tmp_path / "build" / "stitched.pdf").write_bytes(b"%PDF-1.4\n")

    monkeypatch.delenv("NOVELLUM_PDF_VIEWER", raising=False)
    monkeypatch.delenv("PDF_VIEWER", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["open", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "No PDF viewer found" in error_output.getvalue()


def test_select_command_prints_iteratively_selected_note_ids(tmp_path: Path, monkeypatch) -> None:
    """``select`` should accumulate note IDs in the order chosen by the user."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
"""
    beta = """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")

    responses = iter(
        [
            "beta\tproof\tBeta\t-\n",
            "alpha\tconcept\tAlpha\t-\n",
            "[done]\tfinish\tfinish selection (2 chosen)\ttype q then enter\n",
        ]
    )

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = next(responses)

        return Result()

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["select", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert output.getvalue().splitlines() == ["beta", "alpha"]


def test_select_command_requires_fzf(tmp_path: Path, monkeypatch) -> None:
    """``select`` should fail cleanly when ``fzf`` is unavailable."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    monkeypatch.setattr("shutil.which", lambda name: None)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["select", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Warning: fzf not found" in error_output.getvalue()
    assert "Interactive selection requires fzf" in error_output.getvalue()


def test_show_reports_missing_note_as_cli_error(tmp_path: Path) -> None:
    """Lookup failures should produce CLI-style stderr output."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["show", "does-not-exist", "--no-interactive", "--cwd", str(tmp_path)])

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
        exit_code = main(["show", "shared", "--no-interactive", "--cwd", str(tmp_path)])

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
        exit_code = main(["show", "duplicate", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Duplicate note ID" in error_output.getvalue()


def test_show_uses_interactive_selection_when_reference_is_omitted(tmp_path: Path, monkeypatch) -> None:
    """``show`` should use ``fzf`` selection by default when no reference is given."""

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
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "alpha\tconcept\tAlpha Note\t-\n"

        return Result()

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["show", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert "Alpha Note" in output.getvalue()


def test_stitch_uses_interactive_multi_selection_when_references_are_omitted(tmp_path: Path, monkeypatch) -> None:
    """``stitch`` should use multi-select ``fzf`` when no references are provided."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
    alpha = """% novellum:begin
% id: alpha
% title: Alpha
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Alpha}
"""
    beta = """% novellum:begin
% id: beta
% title: Beta
% type: proof
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Beta}
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "beta\tproof\tBeta\t-\nalpha\tconcept\tAlpha\t-\n"

        return Result()

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    exit_code = main(["stitch", "--cwd", str(tmp_path)])
    stitched_text = (tmp_path / "build" / "stitched.tex").read_text(encoding="utf-8")

    assert exit_code == 0
    assert stitched_text.index("% note: beta") < stitched_text.index("% note: alpha")


def test_interactive_commands_warn_and_fall_back_when_fzf_is_missing(tmp_path: Path, monkeypatch) -> None:
    """Missing ``fzf`` should warn, then fall back to the old required-argument behavior."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    monkeypatch.setattr("shutil.which", lambda name: None)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["show", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Warning: fzf not found" in error_output.getvalue()
    assert "Provide a note reference" in error_output.getvalue()


def test_no_interactive_requires_reference_for_single_note_commands(tmp_path: Path) -> None:
    """``--no-interactive`` should keep the old required-reference behavior."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["show", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide a note reference" in error_output.getvalue()
