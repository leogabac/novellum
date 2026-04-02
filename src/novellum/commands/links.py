from __future__ import annotations

from pathlib import Path

from novellum.index import build_index, find_note
from novellum.storage import find_workspace


def links_command(reference: str, cwd: Path = Path(".")) -> int:
    workspace = find_workspace(cwd)
    index = build_index(workspace)
    note = find_note(index, reference)

    print(f"Note: {note.metadata.id}")
    print("Outbound:")
    outbound = index.outbound[note.metadata.id]
    if not outbound:
        print("- none")
    else:
        for link in outbound:
            if link.resolved_id is None:
                print(f"- {link.target} [unresolved]")
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
