"""Implementation of the ``novellum compile`` command."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from novellum.storage import find_workspace, load_config


def compile_command(
    target: str = "workspace",
    cwd: Path = Path("."),
) -> int:
    """Compile a workspace or stitched LaTeX document with ``latexmk``.

    Parameters
    ----------
    target : str, optional
        Either ``workspace``, ``stitched``, or a relative/absolute ``.tex``
        path to compile.
    cwd : Path, optional
        Path used for workspace discovery.

    Returns
    -------
    int
        Process-style exit code.
    """

    workspace = find_workspace(cwd)
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        raise RuntimeError("latexmk is not installed or not available on PATH.")

    source_path = _resolve_compile_target(workspace.root, workspace.build_dir, target, load_config(workspace))
    if not source_path.exists():
        raise FileNotFoundError(f"Compile target does not exist: {source_path.relative_to(workspace.root)}")

    relative_source = source_path.relative_to(workspace.root)
    command = [
        latexmk,
        "-pdf",
        "-interaction=nonstopmode",
        f"-output-directory={workspace.build_dir.relative_to(workspace.root)}",
        str(relative_source),
    ]
    subprocess.run(command, check=True, cwd=workspace.root)
    print(f"Compiled {relative_source} into {workspace.build_dir.relative_to(workspace.root)}")
    return 0


def _resolve_compile_target(root: Path, build_dir: Path, target: str, config: dict) -> Path:
    """Resolve a compile target string into an absolute ``.tex`` path."""

    if target == "workspace":
        return root / config["workspace"]["workspace_root"]
    if target == "stitched":
        return build_dir / "stitched.tex"

    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate
