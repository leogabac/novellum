"""Implementation of the ``novellum compile`` command."""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess

from novellum.logging import get_cli_logger, time_status
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

    logger = get_cli_logger("novellum.compile")
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
    logger.info("Compiling %s into %s", display_target, display_output)
    try:
        with time_status(f"latexmk {display_target}", logger):
            subprocess.run(command, check=True, cwd=command_cwd)
    except subprocess.CalledProcessError as error:
        if source_path.name == "stitched.tex":
            message = _diagnose_stitched_compile_failure(workspace, source_path)
            if message is not None:
                raise RuntimeError(message) from error
        raise RuntimeError(f"latexmk failed while compiling {display_target}. Check the LaTeX log for details.") from error
    logger.info("Compiled %s into %s", display_target, display_output)
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


def _diagnose_stitched_compile_failure(workspace, source_path: Path) -> str | None:
    """Provide a clearer error for common stitched-document failures."""

    log_path = source_path.with_suffix(".log")
    preamble_path = workspace.tex_dir / "stitched-preamble.tex"
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    undefined_macros = _extract_undefined_macros(log_text)

    if not undefined_macros:
        return None

    if preamble_path.exists() and _preamble_has_no_active_content(preamble_path):
        commands = ", ".join(f"\\{name}" for name in undefined_macros[:5])
        return (
            "Stitched document compilation failed because "
            f"{preamble_path.relative_to(workspace.root)} only contains comments, "
            f"but the stitched notes use commands such as {commands}. "
            "Add the required packages to that file. For example, physics-style commands "
            "like \\dv, \\qty, or \\grad require an active line such as \\usepackage{physics}."
        )

    commands = ", ".join(f"\\{name}" for name in undefined_macros[:5])
    return (
        "Stitched document compilation failed due to undefined LaTeX commands "
        f"({commands}). Check {preamble_path.relative_to(workspace.root)} and ensure it loads "
        "the packages needed by the stitched notes."
    )


def _extract_undefined_macros(log_text: str) -> list[str]:
    """Extract undefined LaTeX command names from a log."""

    matches = re.findall(r"^l\.\d+\s+\\([A-Za-z@]+)", log_text, flags=re.MULTILINE)
    seen: list[str] = []
    for name in matches:
        if name not in seen:
            seen.append(name)
    return seen


def _preamble_has_no_active_content(path: Path) -> bool:
    """Return true when the preamble file only contains comments or blank lines."""

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("%"):
            return False
    return True
