"""Workspace and note storage helpers.

This module owns the filesystem conventions of a Novellum workspace. The rest
of the application relies on these helpers to discover the workspace, create
notes, and load templates without needing to know the on-disk layout directly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import re
import shutil
import tomllib

from novellum.models import Note, NoteMetadata, Workspace
from novellum.parser import parse_note_text, render_note_text

DEFAULT_NOTE_TYPES = ("concept", "proof", "paper", "experiment", "question", "log", "ref")
WORKSPACE_MARKER = ".novellum"
CONFIG_FILE = "config.toml"
PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATES_DIR = PACKAGE_ROOT / "templates"
DEFAULT_TEX_DIR = PACKAGE_ROOT / "tex"
DEFAULT_BIBLIOGRAPHY_DIR = PACKAGE_ROOT / "bibliography"


def init_workspace(root: Path) -> Workspace:
    """Initialize a Novellum workspace at ``root``.

    Parameters
    ----------
    root : Path
        Target directory for the workspace.

    Returns
    -------
    Workspace
        Resolved workspace paths after initialization.
    """

    root = root.resolve()
    config_dir = root / WORKSPACE_MARKER
    notes_dir = root / "notes"
    build_dir = root / "build"
    bibliography_dir = root / "bibliography"
    tex_dir = root / "tex"
    templates_dir = config_dir / "templates"

    # The initializer is idempotent. Existing workspaces keep their files and
    # only receive missing defaults.
    config_dir.mkdir(parents=True, exist_ok=True)
    notes_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)
    bibliography_dir.mkdir(parents=True, exist_ok=True)
    tex_dir.mkdir(parents=True, exist_ok=True)
    templates_dir.mkdir(parents=True, exist_ok=True)

    for note_type in DEFAULT_NOTE_TYPES:
        (notes_dir / note_type).mkdir(parents=True, exist_ok=True)

    config_path = config_dir / CONFIG_FILE
    if not config_path.exists():
        config_path.write_text(_default_config_text(), encoding="utf-8")

    for template in DEFAULT_TEMPLATES_DIR.glob("*.tex"):
        destination = templates_dir / template.name
        if not destination.exists():
            shutil.copyfile(template, destination)

    for tex_asset in DEFAULT_TEX_DIR.glob("*.tex"):
        destination = tex_dir / tex_asset.name
        if not destination.exists():
            shutil.copyfile(tex_asset, destination)

    style_asset = DEFAULT_TEX_DIR / "novellum.sty"
    style_destination = tex_dir / style_asset.name
    if not style_destination.exists():
        shutil.copyfile(style_asset, style_destination)

    for bibliography_asset in DEFAULT_BIBLIOGRAPHY_DIR.glob("*.bib"):
        destination = bibliography_dir / bibliography_asset.name
        if not destination.exists():
            shutil.copyfile(bibliography_asset, destination)

    return Workspace(
        root=root,
        config_dir=config_dir,
        notes_dir=notes_dir,
        build_dir=build_dir,
        bibliography_dir=bibliography_dir,
        templates_dir=templates_dir,
        tex_dir=tex_dir,
    )


def find_workspace(start: Path) -> Workspace:
    """Find the nearest Novellum workspace by walking upward from ``start``.

    Parameters
    ----------
    start : Path
        Starting location for workspace discovery.

    Returns
    -------
    Workspace
        Resolved workspace object for the first matching parent.

    Raises
    ------
    FileNotFoundError
        Raised when no ``.novellum`` directory exists in the search path.
    """

    current = start.resolve()
    for candidate in (current, *current.parents):
        config_dir = candidate / WORKSPACE_MARKER
        if config_dir.is_dir():
            return Workspace(
                root=candidate,
                config_dir=config_dir,
                notes_dir=candidate / "notes",
                build_dir=candidate / "build",
                bibliography_dir=candidate / "bibliography",
                templates_dir=config_dir / "templates",
                tex_dir=candidate / "tex",
            )
    raise FileNotFoundError("No novellum workspace found. Run 'novellum init' first.")


def load_config(workspace: Workspace) -> dict:
    """Load the TOML configuration for a workspace.

    Parameters
    ----------
    workspace : Workspace
        Workspace whose config should be loaded.

    Returns
    -------
    dict
        Parsed TOML configuration as nested Python dictionaries.
    """

    config_path = workspace.config_dir / CONFIG_FILE
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def get_note_types(workspace: Workspace) -> tuple[str, ...]:
    """Return the configured note types for a workspace."""

    config = load_config(workspace)
    return tuple(config["workspace"]["note_types"])


def create_note(
    workspace: Workspace,
    title: str,
    note_type: str,
    note_id: str | None = None,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
) -> Path:
    """Create a new note file from workspace defaults and templates.

    Parameters
    ----------
    workspace : Workspace
        Target workspace.
    title : str
        Human-readable title for the note.
    note_type : str
        Note category to place the file under.
    note_id : str or None, optional
        Explicit stable note identifier. If omitted, a slug is derived from the
        title.
    tags : list[str] or None, optional
        Optional tags to record in metadata.
    aliases : list[str] or None, optional
        Optional alternate references for note lookup.

    Returns
    -------
    Path
        Path to the newly created note file.

    Raises
    ------
    ValueError
        Raised when the note type is not part of the workspace configuration.
    FileExistsError
        Raised when a note with the resolved ID already exists anywhere in the
        workspace.
    """

    note_types = get_note_types(workspace)
    if note_type not in note_types:
        raise ValueError(f"Unknown note type '{note_type}'. Allowed types: {', '.join(note_types)}")

    created_at = _utc_now()
    resolved_id = note_id or slugify(title)
    note_path = workspace.notes_dir / note_type / f"{resolved_id}.tex"
    existing_note = find_note_path_by_id(workspace, resolved_id)

    if existing_note is not None:
        raise FileExistsError(
            f"Note ID '{resolved_id}' already exists at {existing_note.relative_to(workspace.root)}"
        )

    metadata = NoteMetadata(
        id=resolved_id,
        title=title,
        note_type=note_type,
        created=created_at,
        updated=created_at,
        tags=tags or [],
        aliases=aliases or [],
    )

    body = load_template(workspace, note_type).format(title=title, id=resolved_id)
    note_path.write_text(render_note_text(metadata, body), encoding="utf-8")
    return note_path


def list_notes(workspace: Workspace, note_type: str | None = None) -> list[Note]:
    """Load notes from the workspace.

    Parameters
    ----------
    workspace : Workspace
        Workspace to scan.
    note_type : str or None, optional
        Optional category filter.

    Returns
    -------
    list[Note]
        Parsed notes sorted by path.
    """

    notes: list[Note] = []
    search_root = workspace.notes_dir / note_type if note_type else workspace.notes_dir
    if not search_root.exists():
        return notes

    for path in sorted(search_root.rglob("*.tex")):
        note = load_note(path)
        notes.append(note)
    return notes


def rename_note(
    workspace: Workspace,
    reference: str,
    new_note_id: str,
    *,
    source_path: Path | None = None,
) -> Path:
    """Rename a note's canonical ID and move the file to match.

    Parameters
    ----------
    workspace : Workspace
        Workspace containing the note.
    reference : str
        Existing canonical note ID to rename.
    new_note_id : str
        New canonical note ID to assign.

    Returns
    -------
    Path
        Path to the renamed note.

    Raises
    ------
    FileNotFoundError
        Raised when the referenced note does not exist.
    FileExistsError
        Raised when another note already uses the requested new ID.
    """

    resolved_source_path = source_path or find_note_path_by_id(workspace, reference)
    if resolved_source_path is None:
        raise FileNotFoundError(f"No note found for '{reference}'.")

    note = load_note(resolved_source_path)
    if note.metadata.id == new_note_id:
        return resolved_source_path

    existing_path = find_note_path_by_id(workspace, new_note_id)
    if existing_path is not None and existing_path != resolved_source_path:
        raise FileExistsError(f"Note ID '{new_note_id}' already exists at {existing_path.relative_to(workspace.root)}")

    note.metadata.id = new_note_id
    note.metadata.updated = _utc_now()
    destination = resolved_source_path.with_name(f"{new_note_id}.tex")
    destination.write_text(render_note_text(note.metadata, note.body), encoding="utf-8")
    if destination != resolved_source_path:
        resolved_source_path.unlink()
    return destination


def move_note(
    workspace: Workspace,
    reference: str,
    new_note_type: str,
    *,
    source_path: Path | None = None,
) -> Path:
    """Move a note to a different note-type directory and update metadata."""

    resolved_source_path = source_path or find_note_path_by_id(workspace, reference)
    if resolved_source_path is None:
        raise FileNotFoundError(f"No note found for '{reference}'.")

    note_types = get_note_types(workspace)
    if new_note_type not in note_types:
        raise ValueError(f"Unknown note type '{new_note_type}'. Allowed types: {', '.join(note_types)}")

    note = load_note(resolved_source_path)
    if note.metadata.note_type == new_note_type:
        return resolved_source_path

    note.metadata.note_type = new_note_type
    note.metadata.updated = _utc_now()
    destination = workspace.notes_dir / new_note_type / resolved_source_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_note_text(note.metadata, note.body), encoding="utf-8")
    if destination != resolved_source_path:
        resolved_source_path.unlink()
    return destination


def delete_note(workspace: Workspace, reference: str, *, source_path: Path | None = None) -> Path:
    """Delete a note file by canonical ID."""

    resolved_source_path = source_path or find_note_path_by_id(workspace, reference)
    if resolved_source_path is None:
        raise FileNotFoundError(f"No note found for '{reference}'.")
    resolved_source_path.unlink()
    return resolved_source_path


def load_note(path: Path) -> Note:
    """Load and parse a single note file.

    Parameters
    ----------
    path : Path
        Note file to parse.

    Returns
    -------
    Note
        Parsed note object.
    """

    return parse_note_text(path.read_text(encoding="utf-8"), path=path)


def find_note_path_by_id(workspace: Workspace, note_id: str) -> Path | None:
    """Find an existing note path by canonical note ID.

    Parameters
    ----------
    workspace : Workspace
        Workspace to scan.
    note_id : str
        Canonical note identifier to look for.

    Returns
    -------
    Path or None
        Matching note path when found, otherwise ``None``.
    """

    for path in sorted(workspace.notes_dir.rglob("*.tex")):
        note = load_note(path)
        if note.metadata.id == note_id:
            return path
    return None


def load_template(workspace: Workspace, note_type: str) -> str:
    """Load the template text for a note type.

    Parameters
    ----------
    workspace : Workspace
        Workspace providing the template directory.
    note_type : str
        Note category whose template should be loaded.

    Returns
    -------
    str
        Template contents. Falls back to ``default.tex`` when a specific
        template does not exist.
    """

    candidate = workspace.templates_dir / f"{note_type}.tex"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    fallback = workspace.templates_dir / "default.tex"
    return fallback.read_text(encoding="utf-8")


def slugify(value: str) -> str:
    """Convert free-form text into a filesystem-safe note identifier.

    Parameters
    ----------
    value : str
        Input text, usually a note title.

    Returns
    -------
    str
        Lowercase hyphenated slug.
    """

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "note"


def _utc_now() -> str:
    """Return the current UTC time in a compact ISO 8601 format."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_config_text() -> str:
    """Render the default workspace configuration file.

    Returns
    -------
    str
        TOML configuration content for a new workspace.
    """

    rendered_types = ", ".join(f'"{note_type}"' for note_type in DEFAULT_NOTE_TYPES)
    return (
        "[workspace]\n"
        'version = "0.1"\n'
        'notes_dir = "notes"\n'
        'build_dir = "build"\n'
        'bibliography = ["bibliography/references.bib"]\n'
        'tex_dir = "tex"\n'
        'workspace_root = "tex/workspace.tex"\n'
        f"note_types = [{rendered_types}]\n"
        'default_link_command = "\\\\nvlink"\n'
    )
