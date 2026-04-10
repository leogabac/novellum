"""Graph export helpers for workspace note relationships."""

from __future__ import annotations

from novellum.index import NoteIndex


def render_mermaid_graph(index: NoteIndex, note_type: str | None = None) -> str:
    """Render the resolved note graph as Mermaid flowchart text."""

    notes = [
        note
        for note in sorted(index.notes_by_id.values(), key=lambda note: note.metadata.id)
        if note_type is None or note.metadata.note_type == note_type
    ]
    included_ids = {note.metadata.id for note in notes}
    node_names = {note_id: f"n{position}" for position, note_id in enumerate(sorted(included_ids))}

    lines = [
        "flowchart LR",
        "",
    ]

    for note in notes:
        label = _mermaid_label(note.metadata.title, note.metadata.note_type, note.metadata.id)
        lines.append(f'    {node_names[note.metadata.id]}["{label}"]')

    if notes:
        lines.append("")

    for source_id in sorted(included_ids):
        for link in index.outbound[source_id]:
            if link.resolved_id is None or link.resolved_id not in included_ids:
                continue
            lines.append(f"    {node_names[source_id]} --> {node_names[link.resolved_id]}")

    return "\n".join(lines).rstrip() + "\n"


def _mermaid_label(title: str, note_type: str, note_id: str) -> str:
    """Build a Mermaid-safe node label."""

    escaped_title = _escape_mermaid(title)
    escaped_type = _escape_mermaid(note_type)
    escaped_id = _escape_mermaid(note_id)
    return f"{escaped_title}<br/>{escaped_type} :: {escaped_id}"


def _escape_mermaid(value: str) -> str:
    """Escape Mermaid label content conservatively."""

    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
