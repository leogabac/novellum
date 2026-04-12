"""Implementation of the ``novellum broken`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import load_index
from novellum.output import emit_json, indexed_link_payload, json_output_enabled, print_empty, print_link_table
from novellum.storage import find_workspace


def broken_command(cwd: Path = Path(".")) -> int:
    """Display unresolved and ambiguous links across the workspace.

    Parameters
    ----------
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    index = load_index(workspace)
    has_broken = any(index.broken_links.values())

    if not has_broken:
        if json_output_enabled():
            emit_json(
                {
                    "ok": True,
                    "command": "broken",
                    "workspace_root": str(workspace.root),
                    "links": [],
                }
            )
            return 0
        print_empty("No broken links found.")
        return 0

    if json_output_enabled():
        links = [
            indexed_link_payload(link)
            for source_id in sorted(index.broken_links)
            for link in index.broken_links[source_id]
        ]
        emit_json(
            {
                "ok": True,
                "command": "broken",
                "workspace_root": str(workspace.root),
                "links": links,
            }
        )
        return 0

    rows: list[tuple[str, str, str, str]] = []
    for source_id in sorted(index.broken_links):
        for link in index.broken_links[source_id]:
            status = "ambiguous" if link.candidate_ids else "missing"
            details = ", ".join(link.candidate_ids) if link.candidate_ids else "-"
            rows.append((source_id, link.target, status, details))
    print_link_table(
        "Broken Links",
        rows,
        empty_message="No broken links found.",
        columns=["Source", "Target", "Kind", "Candidates"],
    )
    return 0
