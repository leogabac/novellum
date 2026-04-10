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
    assert "Created note notes/concept/spectral-gap.tex" in new_output.getvalue()
    assert "Notes" in list_output.getvalue()
    assert "spectral-gap" in list_output.getvalue()


def test_ls_alias_lists_notes_in_workspace(tmp_path: Path) -> None:
    """``ls`` should act as an alias for ``list``."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    with redirect_stdout(io.StringIO()):
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["ls", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert "Notes" in output.getvalue()
    assert "spectral-gap" in output.getvalue()


def test_list_command_supports_plain_output(tmp_path: Path) -> None:
    """``--plain`` should disable Rich table rendering for shared list output."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["--plain", "list", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert "Notes" in output.getvalue()
    assert "ID\tTYPE\tTITLE\tLINKS\tPATH" in output.getvalue()
    assert "spectral-gap" in output.getvalue()


def test_rename_command_updates_note_id_and_filename(tmp_path: Path) -> None:
    """``rename`` should move the file and update the stored metadata ID."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["rename", "spectral-gap", "spectral-gap-notes", "--cwd", str(tmp_path)])

    renamed_path = tmp_path / "notes" / "concept" / "spectral-gap-notes.tex"
    renamed_text = renamed_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert renamed_path.exists()
    assert not (tmp_path / "notes" / "concept" / "spectral-gap.tex").exists()
    assert "% id: spectral-gap-notes" in renamed_text
    assert "Renamed note to notes/concept/spectral-gap-notes.tex" in output.getvalue()


def test_rename_command_can_select_and_prompt_interactively(tmp_path: Path, monkeypatch) -> None:
    """``rename`` should support fzf selection plus questionary input."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "spectral-gap\tconcept\tSpectral Gap\t-\n"

        return Result()

    class Prompt:
        def ask(self) -> str:
            return "spectral-gap-notes"

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("novellum.commands.rename_note.questionary.text", lambda *args, **kwargs: Prompt())

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["rename", "--cwd", str(tmp_path)])

    renamed_path = tmp_path / "notes" / "concept" / "spectral-gap-notes.tex"
    assert exit_code == 0
    assert renamed_path.exists()
    assert "Renamed note to notes/concept/spectral-gap-notes.tex" in output.getvalue()


def test_rename_command_reports_duplicate_target_ids(tmp_path: Path) -> None:
    """``rename`` should fail clearly when the target ID is already taken."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Alpha", "--type", "concept", "--id", "alpha", "--cwd", str(tmp_path)])
        main(["new", "Beta", "--type", "proof", "--id", "beta", "--cwd", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["rename", "alpha", "beta", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Note ID 'beta' already exists" in error_output.getvalue()


def test_rename_command_rewrites_inbound_links_by_default(tmp_path: Path) -> None:
    """``rename`` should update inbound ``\\nvlink`` targets by default."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Alpha", "--type", "concept", "--id", "alpha", "--cwd", str(tmp_path)])
        main(["new", "Beta", "--type", "proof", "--id", "beta", "--cwd", str(tmp_path)])

    inbound_path = tmp_path / "notes" / "proof" / "beta.tex"
    inbound_path.write_text(
        (
            "% novellum:begin\n"
            "% id: beta\n"
            "% title: Beta\n"
            "% type: proof\n"
            "% created: 2026-01-01T00:00:00Z\n"
            "% updated: 2026-01-01T00:00:00Z\n"
            "% tags: \n"
            "% aliases: \n"
            "% novellum:end\n\n"
            "\\section{Beta}\n"
            "\\nvlink{alpha}\n"
            "\\nvlink[Alpha label]{alpha}\n"
            "% \\nvlink{alpha}\n"
        ),
        encoding="utf-8",
    )

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["rename", "alpha", "gamma", "--cwd", str(tmp_path)])

    updated_text = inbound_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "\\nvlink{gamma}" in updated_text
    assert "\\nvlink[Alpha label]{gamma}" in updated_text
    assert "% \\nvlink{alpha}" in updated_text
    assert "rewrote inbound links" in output.getvalue()


def test_rename_command_can_skip_inbound_link_rewrites(tmp_path: Path) -> None:
    """``rename --no-rewrite-links`` should leave inbound links unchanged."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Alpha", "--type", "concept", "--id", "alpha", "--cwd", str(tmp_path)])
        main(["new", "Beta", "--type", "proof", "--id", "beta", "--cwd", str(tmp_path)])

    inbound_path = tmp_path / "notes" / "proof" / "beta.tex"
    inbound_path.write_text(
        (
            "% novellum:begin\n"
            "% id: beta\n"
            "% title: Beta\n"
            "% type: proof\n"
            "% created: 2026-01-01T00:00:00Z\n"
            "% updated: 2026-01-01T00:00:00Z\n"
            "% tags: \n"
            "% aliases: \n"
            "% novellum:end\n\n"
            "\\section{Beta}\n"
            "\\nvlink{alpha}\n"
        ),
        encoding="utf-8",
    )

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["rename", "alpha", "gamma", "--no-rewrite-links", "--cwd", str(tmp_path)])

    updated_text = inbound_path.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "\\nvlink{alpha}" in updated_text
    assert "rewrote inbound links" not in output.getvalue()


def test_rename_command_dry_run_previews_changes_without_writing(tmp_path: Path) -> None:
    """``rename --dry-run`` should preview file and link changes without applying them."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Alpha", "--type", "concept", "--id", "alpha", "--cwd", str(tmp_path)])
        main(["new", "Beta", "--type", "proof", "--id", "beta", "--cwd", str(tmp_path)])

    inbound_path = tmp_path / "notes" / "proof" / "beta.tex"
    inbound_path.write_text(
        (
            "% novellum:begin\n"
            "% id: beta\n"
            "% title: Beta\n"
            "% type: proof\n"
            "% created: 2026-01-01T00:00:00Z\n"
            "% updated: 2026-01-01T00:00:00Z\n"
            "% tags: \n"
            "% aliases: \n"
            "% novellum:end\n\n"
            "\\section{Beta}\n"
            "\\nvlink{alpha}\n"
        ),
        encoding="utf-8",
    )

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["rename", "alpha", "gamma", "--dry-run", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "notes" / "concept" / "alpha.tex").exists()
    assert not (tmp_path / "notes" / "concept" / "gamma.tex").exists()
    assert "\\nvlink{alpha}" in inbound_path.read_text(encoding="utf-8")
    rendered = output.getvalue()
    assert "Dry run: would rename notes/concept/alpha.tex to notes/concept/gamma.tex" in rendered
    assert "Dry run: would rewrite inbound links in 1 note(s)" in rendered
    assert "notes/proof/beta.tex" in rendered


def test_rename_command_no_interactive_requires_reference_and_new_id(tmp_path: Path) -> None:
    """``rename --no-interactive`` should require both arguments explicitly."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["rename", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide a note reference" in error_output.getvalue()


def test_rename_command_no_interactive_requires_new_id(tmp_path: Path) -> None:
    """``rename --no-interactive`` should fail when the new ID is omitted."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["rename", "spectral-gap", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide a new note ID" in error_output.getvalue()


def test_move_command_updates_note_type_and_directory(tmp_path: Path) -> None:
    """``move`` should relocate the note and update its metadata type."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["move", "spectral-gap", "proof", "--cwd", str(tmp_path)])

    moved_path = tmp_path / "notes" / "proof" / "spectral-gap.tex"
    moved_text = moved_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert moved_path.exists()
    assert not (tmp_path / "notes" / "concept" / "spectral-gap.tex").exists()
    assert "% type: proof" in moved_text
    assert "Moved spectral-gap (Spectral Gap) to [proof] at notes/proof/spectral-gap.tex" in output.getvalue()


def test_move_command_can_select_and_prompt_interactively(tmp_path: Path, monkeypatch) -> None:
    """``move`` should support interactive note and destination selection."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "spectral-gap\tconcept\tSpectral Gap\t-\n"

        return Result()

    class Prompt:
        def ask(self) -> str:
            return "proof"

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("novellum.commands.move_note.questionary.select", lambda *args, **kwargs: Prompt())

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["move", "--cwd", str(tmp_path)])

    moved_path = tmp_path / "notes" / "proof" / "spectral-gap.tex"
    assert exit_code == 0
    assert moved_path.exists()
    assert "Moved spectral-gap (Spectral Gap) to [proof] at notes/proof/spectral-gap.tex" in output.getvalue()


def test_move_command_no_interactive_requires_reference(tmp_path: Path) -> None:
    """``move --no-interactive`` should require the source note explicitly."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["move", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide a note reference" in error_output.getvalue()


def test_move_command_no_interactive_requires_destination_type(tmp_path: Path) -> None:
    """``move --no-interactive`` should require the destination type explicitly."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["move", "spectral-gap", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide a destination note type" in error_output.getvalue()


def test_delete_command_removes_note_with_yes_flag(tmp_path: Path) -> None:
    """``delete --yes`` should remove the note without prompting."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["delete", "spectral-gap", "--yes", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert not (tmp_path / "notes" / "concept" / "spectral-gap.tex").exists()
    rendered = output.getvalue()
    assert "Deleting spectral-gap (Spectral Gap) [concept] at notes/concept/spectral-gap.tex" in rendered
    assert "Deleted spectral-gap (Spectral Gap) [concept] from notes/concept/spectral-gap.tex" in rendered


def test_delete_command_can_select_and_confirm_interactively(tmp_path: Path, monkeypatch) -> None:
    """``delete`` should support interactive note selection and confirmation."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "spectral-gap\tconcept\tSpectral Gap\t-\n"

        return Result()

    class Prompt:
        def ask(self) -> bool:
            return True

    prompts: list[str] = []

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        "novellum.commands.delete_note.questionary.confirm",
        lambda message, **kwargs: prompts.append(message) or Prompt(),
    )

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["delete", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert not (tmp_path / "notes" / "concept" / "spectral-gap.tex").exists()
    assert prompts == ["Delete spectral-gap (Spectral Gap) [concept] at notes/concept/spectral-gap.tex?"]
    assert "Deleted spectral-gap (Spectral Gap) [concept] from notes/concept/spectral-gap.tex" in output.getvalue()


def test_delete_command_no_interactive_requires_reference(tmp_path: Path) -> None:
    """``delete --no-interactive`` should require the source note explicitly."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["delete", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide a note reference" in error_output.getvalue()


def test_delete_command_no_interactive_requires_yes_flag(tmp_path: Path) -> None:
    """``delete --no-interactive`` should require explicit confirmation."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["delete", "spectral-gap", "--no-interactive", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Pass --yes to confirm deletion" in error_output.getvalue()


def test_delete_command_reports_cancelled_confirmation(tmp_path: Path, monkeypatch) -> None:
    """Interactive delete should abort cleanly when confirmation is declined."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    class Prompt:
        def ask(self) -> bool:
            return False

    monkeypatch.setattr("novellum.commands.delete_note.questionary.confirm", lambda *args, **kwargs: Prompt())

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["delete", "spectral-gap", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert (tmp_path / "notes" / "concept" / "spectral-gap.tex").exists()
    assert "Deletion cancelled." in error_output.getvalue()


def test_retag_command_updates_note_tags(tmp_path: Path) -> None:
    """``retag`` should replace the note's tag list."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--tag", "old", "--cwd", str(tmp_path)])

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(
            ["retag", "spectral-gap", "--tag", "analysis", "--tag", "operator-theory", "--cwd", str(tmp_path)]
        )

    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert exit_code == 0
    assert "% tags: analysis, operator-theory" in note_text
    assert (
        "Retagged spectral-gap (Spectral Gap) at notes/concept/spectral-gap.tex -> analysis, operator-theory"
        in output.getvalue()
    )


def test_retag_command_can_prompt_interactively(tmp_path: Path, monkeypatch) -> None:
    """``retag`` should support interactive selection and tag prompting."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--cwd", str(tmp_path)])

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "spectral-gap\tconcept\tSpectral Gap\t-\n"

        return Result()

    class Prompt:
        def ask(self) -> str:
            return "analysis, operator-theory"

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("novellum.commands.retag_note.questionary.text", lambda *args, **kwargs: Prompt())

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["retag", "--cwd", str(tmp_path)])

    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert exit_code == 0
    assert "% tags: analysis, operator-theory" in note_text
    assert (
        "Retagged spectral-gap (Spectral Gap) at notes/concept/spectral-gap.tex -> analysis, operator-theory"
        in output.getvalue()
    )


def test_tag_add_and_remove_commands_update_metadata(tmp_path: Path) -> None:
    """Tag helpers should update note tags through the CLI."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--tag", "analysis", "--cwd", str(tmp_path)])

    with redirect_stdout(io.StringIO()):
        add_exit_code = main(["tag", "add", "spectral-gap", "operator-theory", "--cwd", str(tmp_path)])
    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert add_exit_code == 0
    assert "% tags: analysis, operator-theory" in note_text

    output = io.StringIO()
    with redirect_stdout(output):
        remove_exit_code = main(["tag", "remove", "spectral-gap", "analysis", "--cwd", str(tmp_path)])
    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert remove_exit_code == 0
    assert "% tags: operator-theory" in note_text
    assert "Removed tag analysis on spectral-gap (Spectral Gap) at notes/concept/spectral-gap.tex" in output.getvalue()


def test_tag_commands_support_interactive_prompts(tmp_path: Path, monkeypatch) -> None:
    """Tag add/remove should support interactive note and tag selection."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--tag", "analysis", "--cwd", str(tmp_path)])

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "spectral-gap\tconcept\tSpectral Gap\t-\n"

        return Result()

    class TextPrompt:
        def ask(self) -> str:
            return "operator-theory"

    class SelectPrompt:
        def ask(self) -> str:
            return "analysis"

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("novellum.commands.tag_note.questionary.text", lambda *args, **kwargs: TextPrompt())

    with redirect_stdout(io.StringIO()):
        add_exit_code = main(["tag", "add", "--cwd", str(tmp_path)])
    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert add_exit_code == 0
    assert "% tags: analysis, operator-theory" in note_text

    monkeypatch.setattr("novellum.commands.tag_note.questionary.select", lambda *args, **kwargs: SelectPrompt())
    output = io.StringIO()
    with redirect_stdout(output):
        remove_exit_code = main(["tag", "remove", "--cwd", str(tmp_path)])
    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert remove_exit_code == 0
    assert "% tags: operator-theory" in note_text
    assert "Removed tag analysis on spectral-gap (Spectral Gap) at notes/concept/spectral-gap.tex" in output.getvalue()


def test_alias_add_and_remove_commands_update_metadata(tmp_path: Path) -> None:
    """Alias helpers should update note aliases through the CLI."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--alias", "sg", "--cwd", str(tmp_path)])

    with redirect_stdout(io.StringIO()):
        add_exit_code = main(["alias", "add", "spectral-gap", "spectral", "--cwd", str(tmp_path)])
    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert add_exit_code == 0
    assert "% aliases: sg, spectral" in note_text

    output = io.StringIO()
    with redirect_stdout(output):
        remove_exit_code = main(["alias", "remove", "spectral-gap", "sg", "--cwd", str(tmp_path)])
    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert remove_exit_code == 0
    assert "% aliases: spectral" in note_text
    assert "Removed alias sg on spectral-gap (Spectral Gap) at notes/concept/spectral-gap.tex" in output.getvalue()


def test_alias_commands_support_interactive_prompts(tmp_path: Path, monkeypatch) -> None:
    """Alias add/remove should support interactive note and alias selection."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])
        main(["new", "Spectral Gap", "--type", "concept", "--alias", "sg", "--cwd", str(tmp_path)])

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        class Result:
            returncode = 0
            stdout = "spectral-gap\tconcept\tSpectral Gap\tsg\n"

        return Result()

    class AddPrompt:
        def ask(self) -> str:
            return "spectral"

    class RemovePrompt:
        def ask(self) -> str:
            return "sg"

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/fzf" if name == "fzf" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr("novellum.commands.alias_note.questionary.text", lambda *args, **kwargs: AddPrompt())

    with redirect_stdout(io.StringIO()):
        add_exit_code = main(["alias", "add", "--cwd", str(tmp_path)])
    assert add_exit_code == 0

    monkeypatch.setattr("novellum.commands.alias_note.questionary.select", lambda *args, **kwargs: RemovePrompt())
    output = io.StringIO()
    with redirect_stdout(output):
        remove_exit_code = main(["alias", "remove", "spectral-gap", "--cwd", str(tmp_path)])

    note_text = (tmp_path / "notes" / "concept" / "spectral-gap.tex").read_text(encoding="utf-8")
    assert remove_exit_code == 0
    assert "% aliases: spectral" in note_text
    assert "Removed alias sg on spectral-gap (Spectral Gap) at notes/concept/spectral-gap.tex" in output.getvalue()


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
    assert "Links: beta" in links_output.getvalue()
    assert "alpha" in links_output.getvalue()
    assert "beta" in links_output.getvalue()
    assert "beta" in search_output.getvalue()


def test_graph_command_renders_mermaid_graph(tmp_path: Path) -> None:
    """``graph`` should emit a Mermaid view of resolved note links."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    note_one = """% novellum:begin
% id: alpha
% title: Alpha Note
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
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
"""
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(note_one, encoding="utf-8")
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(note_two, encoding="utf-8")

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["graph", "--cwd", str(tmp_path)])

    assert exit_code == 0
    assert "flowchart LR" in output.getvalue()
    assert "Alpha Note<br/>concept :: alpha" in output.getvalue()
    assert "Beta Note<br/>proof :: beta" in output.getvalue()
    assert "-->" in output.getvalue()


def test_graph_command_can_write_filtered_output(tmp_path: Path) -> None:
    """``graph`` should support category filtering and file output."""

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

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["graph", "--type", "concept", "--output", "build/graph.mmd", "--cwd", str(tmp_path)])

    graph_path = tmp_path / "build" / "graph.mmd"
    graph_text = graph_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert graph_path.exists()
    assert "build/graph.mmd" in output.getvalue()
    assert "Alpha<br/>concept :: alpha" in graph_text
    assert "Beta<br/>proof :: beta" not in graph_text


def test_graph_command_can_render_with_mermaid_cli(tmp_path: Path, monkeypatch) -> None:
    """``graph --render`` should call ``mmdc`` and write a rendered artifact."""

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

    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool, cwd: Path) -> None:
        captured["command"] = command
        captured["check"] = check
        captured["cwd"] = cwd
        Path(command[4]).write_text("<svg></svg>", encoding="utf-8")

    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/mmdc" if name == "mmdc" else None)
    monkeypatch.setattr(subprocess, "run", fake_run)

    output = io.StringIO()
    with redirect_stdout(output):
        exit_code = main(["graph", "--render", "svg", "--cwd", str(tmp_path)])

    graph_path = tmp_path / "build" / "graph.svg"
    assert exit_code == 0
    assert graph_path.exists()
    assert captured["command"][0] == "/usr/bin/mmdc"
    assert captured["command"][1:3] == ["-i", captured["command"][2]]
    assert captured["command"][3:5] == ["-o", str(graph_path)]
    assert captured["check"] is True
    assert captured["cwd"] == tmp_path
    assert "Rendered graph to build/graph.svg" in output.getvalue()


def test_graph_command_reports_missing_mermaid_cli(tmp_path: Path, monkeypatch) -> None:
    """``graph --render`` should fail clearly when ``mmdc`` is unavailable."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    monkeypatch.setattr("shutil.which", lambda name: None)

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["graph", "--render", "svg", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "mmdc is not installed" in error_output.getvalue()


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
    assert "Backlinks: alpha" in backlinks_output.getvalue()
    assert "Alpha Ref" in backlinks_output.getvalue()
    assert "missing" in broken_output.getvalue()
    assert "shared" in broken_output.getvalue()
    assert "delta, gamma" in broken_output.getvalue()


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


def test_stitch_command_can_render_selected_categories(tmp_path: Path) -> None:
    """Category flags should stitch every note from the requested note types."""

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

    with redirect_stdout(io.StringIO()):
        exit_code = main(["stitch", "--concepts", "--experiments", "--cwd", str(tmp_path)])

    stitched_text = (tmp_path / "build" / "stitched.tex").read_text(encoding="utf-8")

    assert exit_code == 0
    assert "% note: alpha" in stitched_text
    assert "% note: gamma" in stitched_text
    assert "% note: beta" not in stitched_text
    assert stitched_text.index("% note: alpha") < stitched_text.index("% note: gamma")


def test_stitch_command_can_mix_references_with_category_flags(tmp_path: Path) -> None:
    """Explicit references should combine with category flags without duplicates."""

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
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% novellum:end

\\section{Gamma}
"""
    (tmp_path / "notes" / "proof" / "beta.tex").write_text(beta, encoding="utf-8")
    (tmp_path / "notes" / "concept" / "alpha.tex").write_text(alpha, encoding="utf-8")
    (tmp_path / "notes" / "concept" / "gamma.tex").write_text(gamma, encoding="utf-8")

    with redirect_stdout(io.StringIO()):
        exit_code = main(["stitch", "beta", "--concepts", "--cwd", str(tmp_path)])

    stitched_text = (tmp_path / "build" / "stitched.tex").read_text(encoding="utf-8")

    assert exit_code == 0
    assert stitched_text.index("% note: beta") < stitched_text.index("% note: alpha")
    assert stitched_text.index("% note: alpha") < stitched_text.index("% note: gamma")
    assert stitched_text.count("% note: beta") == 1


def test_stitch_command_requires_references_or_all(tmp_path: Path) -> None:
    """``stitch`` should fail clearly when no note selection is provided."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["stitch", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Provide note references, pass category flags, use --all, or install fzf" in error_output.getvalue()


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
    assert "Use either explicit note references/category flags or --all" in error_output.getvalue()


def test_stitch_command_rejects_category_flags_with_all(tmp_path: Path) -> None:
    """``stitch`` should reject mixing category flags with ``--all``."""

    with redirect_stdout(io.StringIO()):
        main(["init", str(tmp_path)])

    error_output = io.StringIO()
    with redirect_stderr(error_output):
        exit_code = main(["stitch", "--all", "--concepts", "--cwd", str(tmp_path)])

    assert exit_code == 1
    assert "Use either explicit note references/category flags or --all" in error_output.getvalue()


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
    assert "Compiling tex/workspace.tex into build" in output.getvalue()
    assert "latexmk tex/workspace.tex completed in" in output.getvalue()
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

    output = io.StringIO()
    with redirect_stdout(output):
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
    assert "Compiling build/stitched.tex into build" in output.getvalue()
    assert "Compiled build/stitched.tex into build" in output.getvalue()


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
    commands: list[list[str]] = []

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        commands.append(command)

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
    assert all("--height=14" in command for command in commands)
    assert all("--layout=reverse" in command for command in commands)
    assert all("--border=rounded" in command for command in commands)
    assert all("--info=inline" in command for command in commands)


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
    captured_command: list[str] = []

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        captured_command[:] = command

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
    assert "--height=14" in captured_command
    assert "--layout=reverse" in captured_command
    assert "--border=rounded" in captured_command
    assert "--info=inline" in captured_command
    assert "note> " in captured_command


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
    captured_command: list[str] = []

    def fake_run(command: list[str], input: str, text: bool, capture_output: bool, check: bool):
        captured_command[:] = command

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
    assert "-m" in captured_command
    assert "--height=14" in captured_command
    assert "--layout=reverse" in captured_command
    assert "--border=rounded" in captured_command
    assert "--info=inline" in captured_command


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
