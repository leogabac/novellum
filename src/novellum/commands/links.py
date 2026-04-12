"""Implementation of the ``novellum links`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
from novellum.output import emit_json, indexed_link_payload, json_output_enabled, print_key_value_panel, print_link_table
from novellum.selection import select_note_reference
from novellum.storage import find_workspace


def links_command(
    reference: str | None = None,
    interactive: bool = True,
    cwd: Path = Path("."),
) -> int:
    """Display outbound links, backlinks, and unresolved links for a note.

    Parameters
    ----------
    reference : str or None, optional
        Note ID or alias. When omitted, interactive selection is attempted.
    interactive : bool, optional
        Whether interactive note selection should be attempted when the
        reference is omitted.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    resolved_reference = reference
    if resolved_reference is None and interactive:
        resolved_reference = select_note_reference(index)
    if resolved_reference is None:
        raise ValueError("Provide a note reference or install fzf for interactive selection.")
    note = find_note(index, resolved_reference)

    outbound = index.outbound[note.metadata.id]
    backlinks = index.backlinks[note.metadata.id]
    broken = index.broken_links[note.metadata.id]

    if json_output_enabled():
        emit_json(
            {
                "ok": True,
                "command": "links",
                "workspace_root": str(workspace.root),
                "note": {
                    "id": note.metadata.id,
                    "title": note.metadata.title,
                    "type": note.metadata.note_type,
                    "path": str(note.path.relative_to(workspace.root)),
                },
                "outbound": [indexed_link_payload(link) for link in outbound],
                "backlinks": [indexed_link_payload(link) for link in backlinks],
                "broken": [indexed_link_payload(link) for link in broken],
            }
        )
        return 0

    print_key_value_panel(
        f"Links: {note.metadata.id}",
        [
            ("Note", note.metadata.id),
            ("Outbound", str(len(outbound))),
            ("Backlinks", str(len(backlinks))),
            ("Broken", str(len(broken))),
        ],
    )

    outbound_rows: list[tuple[str, str, str]] = []
    for link in outbound:
        if link.resolved_id is not None:
            outbound_rows.append((link.target, link.resolved_id, "resolved"))
            continue
        if link.candidate_ids:
            outbound_rows.append((link.target, ", ".join(link.candidate_ids), "ambiguous"))
        else:
            outbound_rows.append((link.target, "-", "missing"))
    print_link_table(
        "Outbound",
        outbound_rows,
        empty_message="No outbound links found.",
        columns=["Target", "Resolved", "Kind"],
    )

    backlink_rows = [(link.source_id, note.metadata.id) for link in backlinks]
    print_link_table(
        "Backlinks",
        backlink_rows,
        empty_message="No backlinks found.",
        columns=["Source", "Resolved"],
    )

    broken_rows = [(link.target,) for link in broken]
    print_link_table(
        "Broken",
        broken_rows,
        empty_message="No broken links found.",
        columns=["Target"],
    )
    return 0
