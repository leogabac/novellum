from __future__ import annotations

from pathlib import Path

from novellum.index import build_index, search_notes
from novellum.storage import find_workspace


def search_command(query: str, cwd: Path = Path(".")) -> int:
    workspace = find_workspace(cwd)
    index = build_index(workspace)
    matches = search_notes(index, query)

    if not matches:
        print("No notes found.")
        return 0

    print("ID\tTYPE\tTITLE\tPATH")
    for note in matches:
        print(
            "\t".join(
                [
                    note.metadata.id,
                    note.metadata.note_type,
                    note.metadata.title,
                    str(note.path.relative_to(workspace.root)),
                ]
            )
        )
    return 0
