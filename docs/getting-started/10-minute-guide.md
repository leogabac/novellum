# 10-Minute Guide

This guide gets a working Novellum notebook on disk quickly.

The target audience is someone who is comfortable in a shell and wants a
workflow that feels closer to a disciplined research notebook than a notes app.

It is the "I need structure, not a startup meditation app with backlinks"
version of onboarding.

## 1. Install It

From the project root:

```sh
pip install -e .
```

Useful companion tools:

* a LaTeX toolchain with `latexmk`
* BibTeX
* an editor configured through `$EDITOR`
* `fzf` for interactive note selection

## 2. Create a Workspace

```sh
novellum init my-notes
cd my-notes
```

This creates a layout like:

```text
.novellum/
notes/
bibliography/
tex/
build/
```

The important idea is simple:

* `notes/` is the source of truth
* `bibliography/references.bib` is shared across the workspace
* `tex/workspace.tex` remains a normal TeX root for editor tooling
* `build/` holds stitched and compiled output

## 3. Make a Few Notes

```sh
novellum new "Spectral Gap" --type concept --alias sg
novellum new "Poincare Lemma" --type proof --id lemma-poincare
novellum log new
```

Each note is just a `.tex` file with a metadata block at the top.

Example:

```tex
% novellum:begin
% id: spectral-gap
% title: Spectral Gap
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% tags: analysis
% aliases: sg
% novellum:end

\section{Spectral Gap}

This connects to \nvlink{lemma-poincare}.
```

## 4. Work Like a Notebook

Use Novellum to browse and inspect your note graph:

```sh
novellum list
novellum show spectral-gap
novellum links spectral-gap
novellum backlinks lemma-poincare
novellum broken
novellum search poincare
```

If `fzf` is installed, commands like `show`, `edit`, `links`, `backlinks`, and
`stitch` can prompt you interactively when you omit note IDs.

That means you can stay in the terminal and still get a pleasant chooser,
instead of manually remembering every note ID.

## 5. Use the Daily Log Flow

Open or create today’s research note:

```sh
EDITOR="nvim" novellum today
```

This is one of the main ergonomic loops in the project: keep theorem scraps,
proof fragments, reading notes, and daily lab-book style updates in the same
workspace.

## 6. Build a Draft Document

Stitch a few notes together:

```sh
novellum stitch spectral-gap lemma-poincare --title "Analysis Draft"
novellum compile stitched
novellum open stitched
```

Or stitch everything:

```sh
novellum stitch --all --title "Notebook Draft"
novellum compile stitched
```

When stitched notes link to other stitched notes, Novellum rewrites those links
into clickable internal PDF hyperlinks... which is really cool and took a headache to implement.

## 7. What to Do Next

After the first 10 minutes, the normal workflow is usually:

* create notes with `novellum new`
* open the daily log with `novellum today`
* connect notes with `\nvlink{...}`
* inspect graph structure with `links`, `backlinks`, and `broken`
* produce ad hoc drafts with `stitch`

If you want a quick sense of where the project is headed, read the
[Roadmap](../roadmap.md).
