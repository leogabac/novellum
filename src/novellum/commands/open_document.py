"""Implementation of the ``novellum open`` command."""

from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import subprocess

from novellum.commands.compile_document import resolve_compiled_pdf
from novellum.storage import find_workspace, load_config


def open_command(target: str = "stitched", cwd: Path = Path(".")) -> int:
    """Open a compiled PDF with the configured viewer.

    Parameters
    ----------
    target : str, optional
        Either ``stitched``, ``workspace``, a ``.tex`` target, or a ``.pdf``
        path.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    pdf_path = resolve_compiled_pdf(workspace.root, workspace.build_dir, target, load_config(workspace))
    if not pdf_path.exists():
        raise FileNotFoundError(f"Compiled PDF does not exist: {pdf_path.relative_to(workspace.root)}")

    viewer = _resolve_pdf_viewer()
    command = [*shlex.split(viewer), str(pdf_path)]
    subprocess.Popen(command, cwd=workspace.root)
    print(f"Opened {pdf_path.relative_to(workspace.root)}")
    return 0


def _resolve_pdf_viewer() -> str:
    """Select a PDF viewer command with user overrides first."""

    configured = os.environ.get("NOVELLUM_PDF_VIEWER") or os.environ.get("PDF_VIEWER")
    if configured and configured.strip():
        return configured.strip()

    for candidate in ("zathura", "xdg-open", "open"):
        resolved = shutil.which(candidate)
        if resolved is not None:
            return resolved

    raise RuntimeError(
        "No PDF viewer found. Set NOVELLUM_PDF_VIEWER or PDF_VIEWER, or install zathura/xdg-open."
    )
