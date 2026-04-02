from __future__ import annotations

from pathlib import Path

from novellum.storage import create_note, find_workspace

def new_command(
    title: str,
    note_type: str = "concept",
    note_id: str | None = None,
    tags: list[str] | None = None,
    alias: list[str] | None = None,
    cwd: Path = Path("."),
) -> int:
    workspace = find_workspace(cwd)
    note_path = create_note(
        workspace,
        title=title,
        note_type=note_type,
        note_id=note_id,
        tags=tags,
        aliases=alias,
    )
    print(f"Created note {note_path.relative_to(workspace.root)}")
    return 0
