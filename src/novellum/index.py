"""Indexing and lookup helpers for the Novellum note graph.

The index is rebuilt from note files when needed. That keeps the source of
truth in the note files themselves while still giving the CLI a single place to
resolve references, backlinks, and search queries.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from novellum.models import Link, Note, NoteMetadata, Workspace
from novellum.storage import list_notes


@dataclass(slots=True)
class IndexedLink:
    """A link enriched with resolution information.

    Parameters
    ----------
    source_id : str
        ID of the note containing the link.
    target : str
        Raw target text from the ``\\nvlink`` command.
    resolved_id : str or None
        Canonical resolved note ID when the target is uniquely resolvable.
    label : str or None, optional
        Optional display label from the source note.
    candidate_ids : list[str], optional
        All candidate note IDs discovered during resolution. This is useful for
        distinguishing missing targets from ambiguous aliases in diagnostics.
    """

    source_id: str
    target: str
    resolved_id: str | None
    label: str | None = None
    candidate_ids: list[str] | None = None


@dataclass(slots=True)
class NoteIndex:
    """In-memory representation of note resolution and graph relationships.

    Parameters
    ----------
    notes_by_id : dict[str, Note]
        Canonical notes keyed by note ID.
    aliases : dict[str, list[str]]
        Alias lookup map. Values remain lists because aliases may be ambiguous.
    outbound : dict[str, list[IndexedLink]]
        Outbound links keyed by source note ID.
    backlinks : dict[str, list[IndexedLink]]
        Incoming links keyed by destination note ID.
    broken_links : dict[str, list[IndexedLink]]
        Unresolved or ambiguous links keyed by source note ID.
    """

    notes_by_id: dict[str, Note]
    aliases: dict[str, list[str]]
    outbound: dict[str, list[IndexedLink]]
    backlinks: dict[str, list[IndexedLink]]
    broken_links: dict[str, list[IndexedLink]]
    note_mtimes: dict[str, int]


def load_index(workspace: Workspace) -> NoteIndex:
    """Load a cached index when valid, otherwise rebuild it.

    Parameters
    ----------
    workspace : Workspace
        Workspace whose note graph should be loaded.

    Returns
    -------
    NoteIndex
        Cached or freshly rebuilt note graph index.
    """

    cache_path = workspace.config_dir / "index.json"
    current_mtimes = _scan_note_mtimes(workspace)

    if cache_path.exists():
        try:
            cached = _load_cached_index(cache_path, workspace)
        except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError):
            cached = None
        if cached is not None and cached.note_mtimes == current_mtimes:
            return cached

    rebuilt = build_index(workspace)
    _write_cached_index(cache_path, workspace, rebuilt)
    return rebuilt


def build_index(workspace: Workspace) -> NoteIndex:
    """Build a note graph index for a workspace.

    Parameters
    ----------
    workspace : Workspace
        Workspace whose notes should be indexed.

    Returns
    -------
    NoteIndex
        Fully populated in-memory index.
    """

    notes = list_notes(workspace)
    note_mtimes = _scan_note_mtimes(workspace)
    return _build_index_from_notes(notes, note_mtimes)


def find_note(index: NoteIndex, reference: str) -> Note:
    """Resolve a user-supplied reference to a single note.

    Parameters
    ----------
    index : NoteIndex
        Index used for note and alias resolution.
    reference : str
        Canonical ID or alias.

    Returns
    -------
    Note
        Resolved note.

    Raises
    ------
    LookupError
        Raised when the reference is missing or ambiguous.
    """

    matches = resolve_reference(reference, index.notes_by_id, index.aliases)
    if not matches:
        raise LookupError(f"No note found for '{reference}'.")
    if len(matches) > 1:
        joined = ", ".join(sorted(matches))
        raise LookupError(f"Reference '{reference}' is ambiguous. Matches: {joined}")
    return index.notes_by_id[matches[0]]


def search_notes(index: NoteIndex, query: str) -> list[Note]:
    """Run a case-insensitive substring search across note content.

    Parameters
    ----------
    index : NoteIndex
        Note index providing notes to search.
    query : str
        User-supplied search term.

    Returns
    -------
    list[Note]
        Matching notes sorted by canonical ID.
    """

    lowered = query.casefold()
    matches: list[Note] = []
    for note in index.notes_by_id.values():
        # Search intentionally spans both metadata and body so a single command
        # can cover titles, tags, aliases, IDs, and free text.
        fields = [
            note.metadata.id,
            note.metadata.title,
            note.metadata.note_type,
            " ".join(note.metadata.tags),
            " ".join(note.metadata.aliases),
            note.body,
        ]
        haystack = "\n".join(fields).casefold()
        if lowered in haystack:
            matches.append(note)
    return sorted(matches, key=lambda note: note.metadata.id)


def resolve_reference(
    reference: str,
    notes_by_id: dict[str, Note],
    aliases: dict[str, list[str]],
) -> list[str]:
    """Resolve a raw reference string to candidate note IDs.

    Parameters
    ----------
    reference : str
        Canonical ID or alias to resolve.
    notes_by_id : dict[str, Note]
        Canonical note mapping.
    aliases : dict[str, list[str]]
        Alias mapping.

    Returns
    -------
    list[str]
        Candidate note IDs. A list of length one means unique resolution.
    """

    if reference in notes_by_id:
        return [reference]
    return sorted(set(aliases.get(reference, [])))


def _build_aliases(notes: list[Note]) -> dict[str, list[str]]:
    """Build the alias lookup map from loaded notes.

    Parameters
    ----------
    notes : list[Note]
        Notes to scan.

    Returns
    -------
    dict[str, list[str]]
        Alias mapping where values are all note IDs that claim the alias.
    """

    aliases: dict[str, list[str]] = {}
    for note in notes:
        for alias in note.metadata.aliases:
            aliases.setdefault(alias, []).append(note.metadata.id)
    return aliases


def _build_notes_by_id(notes: list[Note]) -> dict[str, Note]:
    """Build the canonical note mapping and reject duplicate IDs.

    Parameters
    ----------
    notes : list[Note]
        Notes to scan.

    Returns
    -------
    dict[str, Note]
        Canonical note mapping.

    Raises
    ------
    ValueError
        Raised when multiple files declare the same canonical note ID.
    """

    notes_by_id: dict[str, Note] = {}
    for note in notes:
        existing = notes_by_id.get(note.metadata.id)
        if existing is not None:
            raise ValueError(
                "Duplicate note ID "
                f"'{note.metadata.id}' found in "
                f"{existing.path} and {note.path}"
            )
        notes_by_id[note.metadata.id] = note
    return notes_by_id


def _scan_note_mtimes(workspace: Workspace) -> dict[str, int]:
    """Collect nanosecond mtimes for note files relative to the workspace."""

    mtimes: dict[str, int] = {}
    for path in sorted(workspace.notes_dir.rglob("*.tex")):
        mtimes[str(path.relative_to(workspace.root))] = path.stat().st_mtime_ns
    return mtimes


def _write_cached_index(cache_path: Path, workspace: Workspace, index: NoteIndex) -> None:
    """Persist a JSON representation of the current index."""

    payload = {
        "note_mtimes": index.note_mtimes,
        "notes": [_serialize_note(note, workspace) for note in index.notes_by_id.values()],
    }
    cache_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _load_cached_index(cache_path: Path, workspace: Workspace) -> NoteIndex:
    """Read a previously persisted index from disk."""

    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    notes = [_deserialize_note(note_data, workspace) for note_data in payload["notes"]]
    note_mtimes = {key: int(value) for key, value in payload["note_mtimes"].items()}
    return _build_index_from_notes(notes, note_mtimes)


def _serialize_note(note: Note, workspace: Workspace) -> dict[str, object]:
    """Convert a note into a JSON-friendly structure."""

    return {
        "path": str(note.path.relative_to(workspace.root)),
        "metadata": {
            "id": note.metadata.id,
            "title": note.metadata.title,
            "note_type": note.metadata.note_type,
            "created": note.metadata.created,
            "updated": note.metadata.updated,
            "tags": note.metadata.tags,
            "aliases": note.metadata.aliases,
        },
        "body": note.body,
        "links": [{"target": link.target, "label": link.label} for link in note.links],
    }


def _deserialize_note(payload: dict[str, object], workspace: Workspace) -> Note:
    """Reconstruct a note from the cached JSON payload."""

    metadata_payload = payload["metadata"]
    if not isinstance(metadata_payload, dict):
        raise TypeError("Invalid cached metadata payload.")

    links_payload = payload["links"]
    if not isinstance(links_payload, list):
        raise TypeError("Invalid cached links payload.")

    return Note(
        path=workspace.root / str(payload["path"]),
        metadata=NoteMetadata(
            id=str(metadata_payload["id"]),
            title=str(metadata_payload["title"]),
            note_type=str(metadata_payload["note_type"]),
            created=str(metadata_payload["created"]),
            updated=str(metadata_payload["updated"]),
            tags=[str(item) for item in metadata_payload["tags"]],
            aliases=[str(item) for item in metadata_payload["aliases"]],
        ),
        body=str(payload["body"]),
        links=[
            Link(target=str(link_payload["target"]), label=_coerce_optional_str(link_payload.get("label")))
            for link_payload in links_payload
            if isinstance(link_payload, dict)
        ],
    )


def _coerce_optional_str(value: object) -> str | None:
    """Normalize cached string fields that may be absent or null."""

    if value is None:
        return None
    return str(value)


def _build_index_from_notes(notes: list[Note], note_mtimes: dict[str, int]) -> NoteIndex:
    """Construct the full derived index from already loaded notes."""

    notes_by_id = _build_notes_by_id(notes)
    aliases = _build_aliases(notes)
    outbound: dict[str, list[IndexedLink]] = {note.metadata.id: [] for note in notes}
    backlinks: dict[str, list[IndexedLink]] = {note.metadata.id: [] for note in notes}
    broken_links: dict[str, list[IndexedLink]] = {note.metadata.id: [] for note in notes}

    for note in notes:
        source_id = note.metadata.id
        for link in note.links:
            matches = resolve_reference(link.target, notes_by_id, aliases)
            resolved_id = matches[0] if len(matches) == 1 else None
            indexed = IndexedLink(
                source_id=source_id,
                target=link.target,
                resolved_id=resolved_id,
                label=link.label,
                candidate_ids=matches,
            )
            outbound[source_id].append(indexed)
            if resolved_id is None:
                broken_links[source_id].append(indexed)
            else:
                backlinks[resolved_id].append(indexed)

    return NoteIndex(
        notes_by_id=notes_by_id,
        aliases=aliases,
        outbound=outbound,
        backlinks=backlinks,
        broken_links=broken_links,
        note_mtimes=note_mtimes,
    )
