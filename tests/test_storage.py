from pathlib import Path

from novellum.storage import create_note, find_workspace, init_workspace, list_notes


def test_init_workspace_creates_novellum_structure(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)

    assert workspace.config_dir == tmp_path / ".novellum"
    assert (tmp_path / ".novellum" / "config.toml").exists()
    assert (tmp_path / ".novellum" / "templates" / "default.tex").exists()
    assert (tmp_path / "notes" / "concept").exists()
    assert (tmp_path / "bibliography" / "references.bib").exists()
    assert (tmp_path / "tex" / "workspace.tex").exists()
    assert (tmp_path / "tex" / "novellum.sty").exists()


def test_create_note_writes_tex_file_with_comment_metadata(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)

    note_path = create_note(workspace, title="Spectral Gap Bound", note_type="concept")
    text = note_path.read_text(encoding="utf-8")

    assert note_path == tmp_path / "notes" / "concept" / "spectral-gap-bound.tex"
    assert text.startswith("% novellum:begin")
    assert "\\section{Spectral Gap Bound}" in text


def test_find_workspace_and_list_notes(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)
    create_note(workspace, title="Alpha", note_type="concept")
    create_note(workspace, title="Beta", note_type="proof")

    nested = tmp_path / "notes" / "proof"
    discovered = find_workspace(nested)
    notes = list_notes(discovered)

    assert discovered.root == tmp_path
    assert len(notes) == 2


def test_init_workspace_writes_vimtex_friendly_config(tmp_path: Path) -> None:
    workspace = init_workspace(tmp_path)
    config_text = (workspace.config_dir / "config.toml").read_text(encoding="utf-8")

    assert 'bibliography = ["bibliography/references.bib"]' in config_text
    assert 'workspace_root = "tex/workspace.tex"' in config_text
