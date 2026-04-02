from __future__ import annotations

from dataclasses import dataclass, field

from novellum.models import Note, Workspace
from novellum.storage import list_notes


@dataclass(slots=True)
class IndexedLink:
    source_id: str
    target: str
    resolved_id: str | None
    label: str | None = None


@dataclass(slots=True)
class NoteIndex:
    notes_by_id: dict[str, Note]
    aliases: dict[str, list[str]]
    outbound: dict[str, list[IndexedLink]]
    backlinks: dict[str, list[IndexedLink]]
    broken_links: dict[str, list[IndexedLink]]


def build_index(workspace: Workspace) -> NoteIndex:
    notes = list_notes(workspace)
    notes_by_id = {note.metadata.id: note for note in notes}
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
    matches = resolve_reference(reference, index.notes_by_id, index.aliases)
    if not matches:
        raise LookupError(f"No note found for '{reference}'.")
    if len(matches) > 1:
        joined = ", ".join(sorted(matches))
        raise LookupError(f"Reference '{reference}' is ambiguous. Matches: {joined}")
    return index.notes_by_id[matches[0]]


def search_notes(index: NoteIndex, query: str) -> list[Note]:
    lowered = query.casefold()
    matches: list[Note] = []
    for note in index.notes_by_id.values():
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
    if reference in notes_by_id:
        return [reference]
    return sorted(set(aliases.get(reference, [])))


def _build_aliases(notes: list[Note]) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    for note in notes:
        for alias in note.metadata.aliases:
            aliases.setdefault(alias, []).append(note.metadata.id)
    return aliases
