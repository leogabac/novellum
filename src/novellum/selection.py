"""Interactive note-selection helpers."""

from __future__ import annotations

import shutil
import subprocess
import sys

from novellum.index import NoteIndex

_FZF_DROPDOWN_OPTIONS = [
    "--height=14",
    "--layout=reverse",
    "--border=rounded",
    "--info=inline",
    "--prompt",
]


def select_note_reference(index: NoteIndex) -> str | None:
    """Select a single note reference via ``fzf`` when available."""

    selected = _run_fzf(index, multi=False)
    if not selected:
        return None
    return selected[0]


def select_note_references(index: NoteIndex) -> list[str] | None:
    """Select multiple note references via ``fzf`` when available."""

    return _run_fzf(index, multi=True)


def select_note_references_iterative(index: NoteIndex) -> list[str] | None:
    """Select note references iteratively via ``fzf`` until the user finishes."""

    fzf = shutil.which("fzf")
    if fzf is None:
        print("Warning: fzf not found; falling back to non-interactive mode.", file=sys.stderr)
        return None

    remaining_ids = sorted(index.notes_by_id)
    selected_ids: list[str] = []
    while remaining_ids:
        lines = [_render_done_choice(len(selected_ids))]
        lines.extend(_render_note_choice(index, note_id) for note_id in remaining_ids)
        result = subprocess.run(
            [
                fzf,
                "--with-nth=2..",
                *_fzf_ui_options(prompt=f"select[{len(selected_ids)}]> "),
            ],
            input="\n".join(lines),
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            break
        selected_line = result.stdout.strip()
        if not selected_line:
            break
        selected_id = selected_line.split("\t", 1)[0]
        if selected_id == "[done]":
            break
        selected_ids.append(selected_id)
        remaining_ids.remove(selected_id)
    return selected_ids


def _run_fzf(index: NoteIndex, multi: bool) -> list[str] | None:
    """Run ``fzf`` over the note list and return selected note IDs."""

    fzf = shutil.which("fzf")
    if fzf is None:
        print("Warning: fzf not found; falling back to non-interactive mode.", file=sys.stderr)
        return None

    lines = [_render_note_choice(index, note_id) for note_id in sorted(index.notes_by_id)]
    command = [fzf]
    if multi:
        command.append("-m")
    command.extend(["--with-nth=2..", *_fzf_ui_options(prompt="note> ")])

    result = subprocess.run(
        command,
        input="\n".join(lines),
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    selected = [line.split("\t", 1)[0] for line in result.stdout.splitlines() if line.strip()]
    return selected


def _render_note_choice(index: NoteIndex, note_id: str) -> str:
    """Render one note choice line for interactive selection."""

    note = index.notes_by_id[note_id]
    aliases = ", ".join(note.metadata.aliases) if note.metadata.aliases else "-"
    return "\t".join([note.metadata.id, note.metadata.note_type, note.metadata.title, aliases])


def _render_done_choice(selected_count: int) -> str:
    """Render the synthetic picker entry that ends iterative selection."""

    return "\t".join(["[done]", "finish", f"finish selection ({selected_count} chosen)", "type q then enter"])


def _fzf_ui_options(*, prompt: str) -> list[str]:
    """Return a consistent inline dropdown-style ``fzf`` layout."""

    return [*_FZF_DROPDOWN_OPTIONS, prompt]
