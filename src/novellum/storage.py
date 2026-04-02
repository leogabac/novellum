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
    root = root.resolve()
    config_dir = root / WORKSPACE_MARKER
    notes_dir = root / "notes"
    build_dir = root / "build"
    bibliography_dir = root / "bibliography"
    tex_dir = root / "tex"
    templates_dir = config_dir / "templates"

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
    config_path = workspace.config_dir / CONFIG_FILE
    return tomllib.loads(config_path.read_text(encoding="utf-8"))


def create_note(
    workspace: Workspace,
    title: str,
    note_type: str,
    note_id: str | None = None,
    tags: list[str] | None = None,
    aliases: list[str] | None = None,
) -> Path:
    config = load_config(workspace)
    note_types = tuple(config["workspace"]["note_types"])
    if note_type not in note_types:
        raise ValueError(f"Unknown note type '{note_type}'. Allowed types: {', '.join(note_types)}")

    created_at = _utc_now()
    resolved_id = note_id or slugify(title)
    note_path = workspace.notes_dir / note_type / f"{resolved_id}.tex"

    if note_path.exists():
        raise FileExistsError(f"Note already exists: {note_path}")

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
    notes: list[Note] = []
    search_root = workspace.notes_dir / note_type if note_type else workspace.notes_dir
    if not search_root.exists():
        return notes

    for path in sorted(search_root.rglob("*.tex")):
        note = load_note(path)
        notes.append(note)
    return notes


def load_note(path: Path) -> Note:
    return parse_note_text(path.read_text(encoding="utf-8"), path=path)


def load_template(workspace: Workspace, note_type: str) -> str:
    candidate = workspace.templates_dir / f"{note_type}.tex"
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    fallback = workspace.templates_dir / "default.tex"
    return fallback.read_text(encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "note"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_config_text() -> str:
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
