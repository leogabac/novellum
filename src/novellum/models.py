"""Core data models used across Novellum.

The project is intentionally small at this stage, so dataclasses provide a
lightweight representation for notes, links, and the workspace layout.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class NoteMetadata:
    """Metadata parsed from the LaTeX comment block at the top of a note.

    Parameters
    ----------
    id : str
        Canonical stable identifier for the note.
    title : str
        Human-readable note title.
    note_type : str
        Logical note category such as ``concept`` or ``proof``.
    created : str
        Creation timestamp in ISO 8601 UTC form.
    updated : str
        Last update timestamp in ISO 8601 UTC form.
    tags : list[str], optional
        Flat tag list used for filtering and search.
    aliases : list[str], optional
        Alternate references that may resolve to this note.
    """

    id: str
    title: str
    note_type: str
    created: str
    updated: str
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Link:
    """A parsed ``\\nvlink`` occurrence inside a note body.

    Parameters
    ----------
    target : str
        Raw target reference found in the LaTeX command.
    label : str or None, optional
        Optional display label supplied through the command's optional
        argument.
    """

    target: str
    label: str | None = None


@dataclass(slots=True)
class Note:
    """A loaded note file with parsed metadata and extracted links.

    Parameters
    ----------
    path : Path
        Filesystem location of the note.
    metadata : NoteMetadata
        Parsed metadata from the leading comment block.
    body : str
        Note body after the metadata block has been removed.
    links : list[Link], optional
        Parsed outbound links found in the body.
    """

    path: Path
    metadata: NoteMetadata
    body: str
    links: list[Link] = field(default_factory=list)


@dataclass(slots=True)
class Workspace:
    """Resolved paths for a Novellum workspace.

    Parameters
    ----------
    root : Path
        Workspace root directory.
    config_dir : Path
        Hidden Novellum configuration directory.
    notes_dir : Path
        Root directory containing note categories and note files.
    build_dir : Path
        Directory reserved for generated outputs.
    bibliography_dir : Path
        Directory containing shared bibliography files.
    templates_dir : Path
        Directory containing note templates copied into the workspace.
    tex_dir : Path
        Directory containing the LaTeX root file and helper package.
    """

    root: Path
    config_dir: Path
    notes_dir: Path
    build_dir: Path
    bibliography_dir: Path
    templates_dir: Path
    tex_dir: Path
