"""Parsing helpers for Novellum note files.

Notes are stored as plain ``.tex`` files. Metadata lives in a leading LaTeX
comment block so the file remains valid and readable LaTeX. Links are encoded
through a dedicated ``\\nvlink`` macro, which lets us stay LaTeX-native while
still exposing explicit graph structure to the CLI.
"""

from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from novellum.models import Link, Note, NoteMetadata

METADATA_BEGIN = "% novellum:begin"
METADATA_END = "% novellum:end"

LINK_PATTERN = re.compile(
    r"\\nvlink(?:\[(?P<label>[^\]]+)])?\{(?P<target>[^{}]+)\}"
)


def parse_note_text(text: str, path: Path) -> Note:
    """Parse a note file into metadata, body, and outbound links.

    Parameters
    ----------
    text : str
        Raw file contents.
    path : Path
        Path associated with the file for diagnostics and note identity.

    Returns
    -------
    Note
        Parsed note representation.
    """

    lines = text.splitlines()
    metadata, body_start = _parse_metadata(lines)
    # The body begins immediately after the metadata terminator. Leading blank
    # lines are stripped so templates render cleanly in command output.
    body = "\n".join(lines[body_start:]).lstrip("\n")
    links = extract_links(body)
    return Note(path=path, metadata=metadata, body=body, links=links)


def extract_links(body: str) -> list[Link]:
    """Extract ``\\nvlink`` targets from a note body.

    Parameters
    ----------
    body : str
        Note body without the metadata block.

    Returns
    -------
    list[Link]
        Parsed link objects in encounter order.
    """

    links: list[Link] = []
    # Comment lines often contain examples in templates. Excluding them keeps
    # instructional comments from polluting the note graph.
    searchable_body = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("%")
    )
    for match in LINK_PATTERN.finditer(searchable_body):
        links.append(Link(target=match.group("target").strip(), label=match.group("label")))
    return links


def render_note_text(metadata: NoteMetadata, body: str) -> str:
    """Render a note back to disk using the Novellum metadata format.

    Parameters
    ----------
    metadata : NoteMetadata
        Metadata to serialize.
    body : str
        LaTeX body content for the note.

    Returns
    -------
    str
        Complete note text ready to be written to a ``.tex`` file.
    """

    meta = asdict(metadata)
    lines = [METADATA_BEGIN]
    for key in ("id", "title", "note_type", "created", "updated", "tags", "aliases"):
        value = meta[key]
        output_key = "type" if key == "note_type" else key
        if isinstance(value, list):
            rendered_value = ", ".join(value)
        else:
            rendered_value = value
        lines.append(f"% {output_key}: {rendered_value}")
    lines.append(METADATA_END)
    lines.append("")
    lines.append(body.rstrip())
    lines.append("")
    return "\n".join(lines)


def _parse_metadata(lines: list[str]) -> tuple[NoteMetadata, int]:
    """Parse the leading metadata block from a note.

    Parameters
    ----------
    lines : list[str]
        Complete note content split into lines.

    Returns
    -------
    tuple[NoteMetadata, int]
        Parsed metadata and the index where the body begins.

    Raises
    ------
    ValueError
        Raised when the note is missing required metadata structure or fields.
    """

    if not lines or lines[0].strip() != METADATA_BEGIN:
        raise ValueError("Note is missing the novellum metadata block.")

    raw: dict[str, str] = {}
    end_index = None

    for index, line in enumerate(lines[1:], start=1):
        stripped = line.strip()
        if stripped == METADATA_END:
            end_index = index
            break
        if not stripped.startswith("% "):
            raise ValueError("Metadata lines must be LaTeX comments beginning with '% '.")
        content = stripped[2:]
        if ":" not in content:
            raise ValueError(f"Invalid metadata line: {line}")
        key, value = content.split(":", 1)
        raw[key.strip()] = value.strip()

    if end_index is None:
        raise ValueError("Note is missing the novellum metadata terminator.")

    required = {"id", "title", "type", "created", "updated"}
    missing = sorted(required - raw.keys())
    if missing:
        raise ValueError(f"Missing required metadata fields: {', '.join(missing)}")

    metadata = NoteMetadata(
        id=raw["id"],
        title=raw["title"],
        note_type=raw["type"],
        created=raw["created"],
        updated=raw["updated"],
        tags=_split_csv(raw.get("tags", "")),
        aliases=_split_csv(raw.get("aliases", "")),
    )
    return metadata, end_index + 1


def _split_csv(value: str) -> list[str]:
    """Parse a comma-separated metadata value into a list.

    Parameters
    ----------
    value : str
        Raw string value from the metadata block.

    Returns
    -------
    list[str]
        Trimmed non-empty items.
    """

    if not value.strip():
        return []
    return [item.strip() for item in value.split(",") if item.strip()]
