"""Indexing and lookup helpers for the Novellum note graph.

The index is rebuilt from note files when needed. That keeps the source of
truth in the note files themselves while still giving the CLI a single place to
resolve references, backlinks, and search queries.
"""

from __future__ import annotations

from dataclasses import dataclass

from novellum.models import Note, Workspace
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
    """

    source_id: str
    target: str
    resolved_id: str | None
    label: str | None = None


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
    notes_by_id = _build_notes_by_id(notes)
    aliases = _build_aliases(notes)
    outbound: dict[str, list[IndexedLink]] = {note.metadata.id: [] for note in notes}
    backlinks: dict[str, list[IndexedLink]] = {note.metadata.id: [] for note in notes}
    broken_links: dict[str, list[IndexedLink]] = {note.metadata.id: [] for note in notes}

    for note in notes:
        source_id = note.metadata.id
        for link in note.links:
            matches = resolve_reference(link.target, notes_by_id, aliases)
            # Only exact or uniquely aliased matches resolve. Ambiguous aliases
            # are intentionally treated the same as broken links so the CLI does
            # not silently guess the wrong target.
            resolved_id = matches[0] if len(matches) == 1 else None
            indexed = IndexedLink(
                source_id=source_id,
                target=link.target,
                resolved_id=resolved_id,
                label=link.label,
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
    )


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
