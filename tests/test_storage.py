"""Tests for workspace initialization and note storage."""

from pathlib import Path
import pytest

from novellum.storage import create_note, find_workspace, init_workspace, list_notes, rename_note


def test_init_workspace_creates_novellum_structure(tmp_path: Path) -> None:
    """Workspace initialization should create the expected directory layout."""

    workspace = init_workspace(tmp_path)

    assert workspace.config_dir == tmp_path / ".novellum"
    assert (tmp_path / ".novellum" / "config.toml").exists()
    assert (tmp_path / ".novellum" / "templates" / "default.tex").exists()
    assert (tmp_path / "notes" / "concept").exists()
    assert (tmp_path / "bibliography" / "references.bib").exists()
    assert (tmp_path / "tex" / "workspace.tex").exists()
    assert (tmp_path / "tex" / "novellum.sty").exists()
    assert (tmp_path / "tex" / "stitched-preamble.tex").exists()


def test_create_note_writes_tex_file_with_comment_metadata(tmp_path: Path) -> None:
    """New notes should be written as ``.tex`` files with comment metadata."""

    workspace = init_workspace(tmp_path)

    note_path = create_note(workspace, title="Spectral Gap Bound", note_type="concept")
    text = note_path.read_text(encoding="utf-8")

    assert note_path == tmp_path / "notes" / "concept" / "spectral-gap-bound.tex"
    assert text.startswith("% novellum:begin")
    assert "\\section{Spectral Gap Bound}" in text


def test_find_workspace_and_list_notes(tmp_path: Path) -> None:
    """Workspace discovery should work from nested directories."""

    workspace = init_workspace(tmp_path)
    create_note(workspace, title="Alpha", note_type="concept")
    create_note(workspace, title="Beta", note_type="proof")

    nested = tmp_path / "notes" / "proof"
    discovered = find_workspace(nested)
    notes = list_notes(discovered)

    assert discovered.root == tmp_path
    assert len(notes) == 2


def test_create_note_rejects_duplicate_ids_across_categories(tmp_path: Path) -> None:
    """Note IDs should be globally unique across the entire workspace."""

    workspace = init_workspace(tmp_path)
    create_note(workspace, title="Alpha", note_type="concept", note_id="shared-id")

    with pytest.raises(FileExistsError, match="shared-id"):
        create_note(workspace, title="Beta", note_type="proof", note_id="shared-id")


def test_init_workspace_writes_vimtex_friendly_config(tmp_path: Path) -> None:
    """New workspaces should include bibliography and LaTeX root settings."""

    workspace = init_workspace(tmp_path)
    config_text = (workspace.config_dir / "config.toml").read_text(encoding="utf-8")

    assert 'bibliography = ["bibliography/references.bib"]' in config_text
    assert 'workspace_root = "tex/workspace.tex"' in config_text


def test_rename_note_updates_metadata_and_filename(tmp_path: Path) -> None:
    """Renaming should rewrite the canonical ID and move the file."""

    workspace = init_workspace(tmp_path)
    original_path = create_note(workspace, title="Alpha", note_type="concept", note_id="alpha")

    renamed_path = rename_note(workspace, reference="alpha", new_note_id="beta")
    renamed_text = renamed_path.read_text(encoding="utf-8")

    assert renamed_path == tmp_path / "notes" / "concept" / "beta.tex"
    assert not original_path.exists()
    assert "% id: beta" in renamed_text
    assert "\\section{Alpha}" in renamed_text


def test_rename_note_rejects_duplicate_target_ids(tmp_path: Path) -> None:
    """Renaming should fail when another note already owns the target ID."""

    workspace = init_workspace(tmp_path)
    create_note(workspace, title="Alpha", note_type="concept", note_id="alpha")
    create_note(workspace, title="Beta", note_type="proof", note_id="beta")

    with pytest.raises(FileExistsError, match="beta"):
        rename_note(workspace, reference="alpha", new_note_id="beta")
