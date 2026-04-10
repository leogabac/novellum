"""Implementation of the ``novellum graph`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.graph import render_mermaid_graph
from novellum.index import load_index
from novellum.storage import find_workspace


def graph_command(
    note_type: str | None = None,
    output_path: Path | None = None,
    cwd: Path = Path("."),
) -> int:
    """Render the workspace note graph as Mermaid text."""

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    rendered = render_mermaid_graph(index, note_type=note_type)

    resolved_output = output_path
    if resolved_output is not None and not resolved_output.is_absolute():
        resolved_output = workspace.root / resolved_output

    if resolved_output is None:
        print(rendered, end="")
        return 0

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(rendered, encoding="utf-8")
    print(f"Wrote graph to {resolved_output.relative_to(workspace.root)}")
    return 0
