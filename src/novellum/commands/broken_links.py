"""Implementation of the ``novellum broken`` command."""

from __future__ import annotations

from pathlib import Path

from novellum.index import load_index
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
        print("No broken links found.")
        return 0

    for source_id in sorted(index.broken_links):
        links = index.broken_links[source_id]
        if not links:
            continue
        print(f"{source_id}:")
        for link in links:
            if link.candidate_ids:
                joined = ", ".join(link.candidate_ids)
                print(f"- {link.target} [ambiguous: {joined}]")
            else:
                print(f"- {link.target} [missing]")
    return 0
