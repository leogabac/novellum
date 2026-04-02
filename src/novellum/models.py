from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class NoteMetadata:
    id: str
    title: str
    note_type: str
    created: str
    updated: str
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Link:
    target: str
    label: str | None = None


@dataclass(slots=True)
class Note:
    path: Path
    metadata: NoteMetadata
    body: str
    links: list[Link] = field(default_factory=list)


@dataclass(slots=True)
class Workspace:
    root: Path
    config_dir: Path
    notes_dir: Path
    build_dir: Path
    bibliography_dir: Path
    templates_dir: Path
    tex_dir: Path
