"""Implementation of the ``novellum links`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import find_note, load_index
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

    print(f"Note: {note.metadata.id}")
    print("Outbound:")
    outbound = index.outbound[note.metadata.id]
    if not outbound:
        print("- none")
    else:
        for link in outbound:
            if link.resolved_id is None:
                if link.candidate_ids:
                    joined = ", ".join(link.candidate_ids)
                    print(f"- {link.target} [ambiguous: {joined}]")
                else:
                    print(f"- {link.target} [missing]")
            else:
                print(f"- {link.target} -> {link.resolved_id}")

    print("Backlinks:")
    backlinks = index.backlinks[note.metadata.id]
    if not backlinks:
        print("- none")
    else:
        for link in backlinks:
            print(f"- {link.source_id} -> {note.metadata.id}")

    print("Broken:")
    broken = index.broken_links[note.metadata.id]
    if not broken:
        print("- none")
    else:
        for link in broken:
            print(f"- {link.target}")
    return 0
