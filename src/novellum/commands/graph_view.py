"""Implementation of the ``novellum graph`` command."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from novellum.graph import render_mermaid_graph
from novellum.index import load_index
from novellum.logging import get_cli_logger
from novellum.storage import find_workspace


def graph_command(
    note_type: str | None = None,
    render_format: str | None = None,
    output_path: Path | None = None,
    cwd: Path = Path("."),
) -> int:
    """Render the workspace note graph as Mermaid text."""

    logger = get_cli_logger("novellum.graph")
    workspace = find_workspace(cwd)
    index = load_index(workspace)
    rendered = render_mermaid_graph(index, note_type=note_type)

    resolved_output = output_path
    if render_format is not None and resolved_output is None:
        resolved_output = workspace.build_dir / f"graph.{render_format}"
    if resolved_output is not None and not resolved_output.is_absolute():
        resolved_output = workspace.root / resolved_output

    if render_format is not None:
        if resolved_output is None:
            raise RuntimeError("Graph rendering requires an output path.")
        return _render_graph_with_mermaid_cli(workspace.root, rendered, resolved_output, logger)

    if resolved_output is None:
        print(rendered, end="")
        return 0

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    resolved_output.write_text(rendered, encoding="utf-8")
    logger.info("Wrote graph to %s", resolved_output.relative_to(workspace.root))
    return 0


def _render_graph_with_mermaid_cli(
    workspace_root: Path,
    graph_text: str,
    output_path: Path,
    logger,
) -> int:
    """Render Mermaid graph text through ``mmdc``."""

    mmdc = shutil.which("mmdc")
    if mmdc is None:
        raise RuntimeError("mmdc is not installed or not available on PATH.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".mmd",
        prefix="novellum-graph-",
        dir=output_path.parent,
        delete=False,
    ) as temporary:
        temporary.write(graph_text)
        temp_path = Path(temporary.name)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".json",
        prefix="novellum-mmdc-",
        dir=output_path.parent,
        delete=False,
    ) as temporary:
        json.dump(
            {
                "args": [
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]
            },
            temporary,
        )
        config_path = Path(temporary.name)

    try:
        logger.info("Rendering graph to %s", output_path.relative_to(workspace_root))
        subprocess.run(
            [mmdc, "-i", str(temp_path), "-o", str(output_path), "-p", str(config_path)],
            check=True,
            cwd=workspace_root,
            text=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        details = ""
        stderr = (error.stderr or "").strip()
        if stderr:
            last_line = stderr.splitlines()[-1]
            details = f" {last_line}"
        raise RuntimeError(
            f"mmdc failed while rendering {output_path.name}."
            " Chromium may be blocked in this environment; try rendering outside a restricted sandbox."
            f"{details}"
        ) from error
    finally:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        try:
            os.unlink(config_path)
        except FileNotFoundError:
            pass

    logger.info("Rendered graph to %s", output_path.relative_to(workspace_root))
    return 0
