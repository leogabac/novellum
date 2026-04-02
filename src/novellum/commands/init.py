from __future__ import annotations

from pathlib import Path

from novellum.storage import init_workspace

def init_command(path: Path = Path(".")) -> int:
    workspace = init_workspace(path)
    print(f"Initialized novellum workspace at {workspace.root}")
    print(f"Workspace config: {workspace.config_dir}")
    print(f"Notes directory: {workspace.notes_dir}")
    return 0
