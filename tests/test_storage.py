"""Tests for workspace initialization and note storage."""

from pathlib import Path
import pytest

from novellum.storage import (
    add_alias_note,
    add_tag_note,
    create_note,
    delete_note,
    find_workspace,
    init_workspace,
    list_notes,
    move_note,
    remove_alias_note,
    remove_tag_note,
    rename_note,
    retag_note,
)


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


def test_rename_note_can_rewrite_inbound_links(tmp_path: Path) -> None:
    """Renaming with link rewriting should update note bodies, not comments."""

    workspace = init_workspace(tmp_path)
    create_note(workspace, title="Alpha", note_type="concept", note_id="alpha")
    inbound_path = create_note(workspace, title="Beta", note_type="proof", note_id="beta")
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

    rename_note(workspace, reference="alpha", new_note_id="gamma", rewrite_links=True)

    updated_text = inbound_path.read_text(encoding="utf-8")
    assert "\\nvlink{gamma}" in updated_text
    assert "\\nvlink[Alpha label]{gamma}" in updated_text
    assert "% \\nvlink{alpha}" in updated_text


def test_move_note_updates_metadata_and_directory(tmp_path: Path) -> None:
    """Moving should rewrite the note type and relocate the file."""

    workspace = init_workspace(tmp_path)
    original_path = create_note(workspace, title="Alpha", note_type="concept", note_id="alpha")

    moved_path = move_note(workspace, reference="alpha", new_note_type="proof")
    moved_text = moved_path.read_text(encoding="utf-8")

    assert moved_path == tmp_path / "notes" / "proof" / "alpha.tex"
    assert not original_path.exists()
    assert "% type: proof" in moved_text
    assert "\\section{Alpha}" in moved_text


def test_delete_note_removes_file(tmp_path: Path) -> None:
    """Deleting should remove the note file from disk."""

    workspace = init_workspace(tmp_path)
    note_path = create_note(workspace, title="Alpha", note_type="concept", note_id="alpha")

    deleted_path = delete_note(workspace, reference="alpha")

    assert deleted_path == note_path
    assert not note_path.exists()


def test_retag_note_replaces_tags(tmp_path: Path) -> None:
    """Retagging should replace the stored tag list."""

    workspace = init_workspace(tmp_path)
    note_path = create_note(workspace, title="Alpha", note_type="concept", note_id="alpha", tags=["old"])

    updated_path = retag_note(workspace, reference="alpha", tags=["analysis", "operator-theory"])
    updated_text = updated_path.read_text(encoding="utf-8")

    assert updated_path == note_path
    assert "% tags: analysis, operator-theory" in updated_text


def test_add_and_remove_alias_note_update_aliases(tmp_path: Path) -> None:
    """Alias helpers should add and remove aliases in metadata."""

    workspace = init_workspace(tmp_path)
    note_path = create_note(workspace, title="Alpha", note_type="concept", note_id="alpha", aliases=["first"])

    add_alias_note(workspace, reference="alpha", alias="second")
    added_text = note_path.read_text(encoding="utf-8")
    assert "% aliases: first, second" in added_text

    remove_alias_note(workspace, reference="alpha", alias="first")
    removed_text = note_path.read_text(encoding="utf-8")
    assert "% aliases: second" in removed_text


def test_add_and_remove_tag_note_update_tags(tmp_path: Path) -> None:
    """Tag helpers should add and remove tags in metadata."""

    workspace = init_workspace(tmp_path)
    note_path = create_note(workspace, title="Alpha", note_type="concept", note_id="alpha", tags=["first"])

    add_tag_note(workspace, reference="alpha", tag="second")
    added_text = note_path.read_text(encoding="utf-8")
    assert "% tags: first, second" in added_text

    remove_tag_note(workspace, reference="alpha", tag="first")
    removed_text = note_path.read_text(encoding="utf-8")
    assert "% tags: second" in removed_text
