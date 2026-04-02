from __future__ import annotations

from pathlib import Path

from novellum.storage import find_workspace, list_notes

def list_command(
    note_type: str | None = None,
    cwd: Path = Path("."),
) -> int:
    workspace = find_workspace(cwd)
    notes = list_notes(workspace, note_type=note_type)

    if not notes:
        print("No notes found.")
        return 0

    print("ID\tTYPE\tTITLE\tLINKS\tPATH")
    for note in notes:
        print(
            "\t".join(
                [
                    note.metadata.id,
                    note.metadata.note_type,
                    note.metadata.title,
                    str(len(note.links)),
                    str(note.path.relative_to(workspace.root)),
                ]
            )
        )
    return 0
