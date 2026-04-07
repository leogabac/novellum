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

    source_path = resolve_compile_target(workspace.root, workspace.build_dir, target, load_config(workspace))
    if not source_path.exists():
        raise FileNotFoundError(f"Compile target does not exist: {source_path.relative_to(workspace.root)}")

    command, command_cwd, display_target, display_output = _build_latexmk_command(
        latexmk=latexmk,
        workspace_root=workspace.root,
        build_dir=workspace.build_dir,
        source_path=source_path,
    )
    subprocess.run(command, check=True, cwd=command_cwd)
    print(f"Compiled {display_target} into {display_output}")
    return 0


def resolve_compile_target(root: Path, build_dir: Path, target: str, config: dict) -> Path:
    """Resolve a compile target string into an absolute ``.tex`` path."""

    if target == "workspace":
        return root / config["workspace"]["workspace_root"]
    if target == "stitched":
        return build_dir / "stitched.tex"

    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate


def resolve_compiled_pdf(root: Path, build_dir: Path, target: str, config: dict) -> Path:
    """Resolve the PDF path expected for a compile target."""

    if target.endswith(".pdf"):
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = root / candidate
        return candidate

    source_path = resolve_compile_target(root, build_dir, target, config)
    if source_path.parent == build_dir:
        return source_path.with_suffix(".pdf")
    return build_dir / f"{source_path.stem}.pdf"


def _build_latexmk_command(
    latexmk: str,
    workspace_root: Path,
    build_dir: Path,
    source_path: Path,
) -> tuple[list[str], Path, str, str]:
    """Build a ``latexmk`` command with cwd/output handling for the target."""

    if source_path.parent == build_dir:
        return (
            [
                latexmk,
                "-pdf",
                "-interaction=nonstopmode",
                "-output-directory=.",
                source_path.name,
            ],
            build_dir,
            str(source_path.relative_to(workspace_root)),
            str(build_dir.relative_to(workspace_root)),
        )

    return (
        [
            latexmk,
            "-pdf",
            "-interaction=nonstopmode",
            f"-output-directory={build_dir.relative_to(workspace_root)}",
            str(source_path.relative_to(workspace_root)),
        ],
        workspace_root,
        str(source_path.relative_to(workspace_root)),
        str(build_dir.relative_to(workspace_root)),
    )
