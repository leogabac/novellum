# novellum

![Static Badge](https://img.shields.io/badge/repo-novellum-blue?logo=github) ![Static Badge](https://img.shields.io/badge/status-dev-red?logo=github)

A CLI linked LaTeX note system for research logbooks.

> [!NOTE]
> This project is still early in development. The current workflow is already usable, but there is still a lot of room to improve and polish.
> If you have ideas, open an _issue_.

`novellum` is for people who want Obsidian-style linking and graph navigation, but do not want to leave normal LaTeX files behind.

Notes are just `.tex` fragments. Metadata lives in a LaTeX comment block. Links use `\nvlink{...}`. Bibliography stays in a shared `references.bib`. The workspace has a normal `tex/workspace.tex` root so editor tooling like VimTeX can still behave like it is inside a regular LaTeX project.

This project exists because I wanted a local-first research notebook that felt more like a pile of theorem scraps, proof fragments, reading notes, and lab notebook entries than a polished notes app.

**Why choose `novellum`?**

You do not have to. I am building this because I am way too opinionated and pedantic on my notes, and it scratches a very specific itch in how I work.

If what you want is:

* plain-text source of truth
* close to LaTeX-native notes
* links, backlinks, broken-link diagnostics
* stitched draft documents
* a CLI workflow that can later integrate with Neovim cleanly

then `novellum` might actually be useful to you.

> [!NOTE]
> The name _novellum_.
> I am obsessed with VTubers, and I put references everythwere I can. It is a mashup of [Shiori Novella](https://www.youtube.com/@ShioriNovella) and a __vellum__.

## Features

* Linked LaTeX notes with metadata stored in comment blocks
* Canonical IDs plus alias-based note resolution
* Search across IDs, titles, tags, aliases, and body text
* Backlinks and broken-link diagnostics
* Research log workflow with dated `log` notes and a `today` command
* Stitched LaTeX output for selected notes or the whole workspace
* Clickable internal note links inside stitched compiled documents
* Workspace root configured for `natbib` and BibTeX instead of `biblatex`/`biber`
* PDF opening through a configurable viewer command
* Default interactive note selection via `fzf`

## Installation

For now, install it with `pip` from the project root:

```sh
pip install .
```

If you are developing locally, the editable install is more convenient:

```sh
pip install -e .
```

You will probably also want:

1. a LaTeX toolchain with `latexmk`
2. BibTeX
3. an editor configured through `$EDITOR`
4. `fzf` if you want the default interactive selection flow

## Quickstart

Create a workspace:

```sh
novellum init my-notes
cd my-notes
```

Create a few notes:

```sh
novellum new "Spectral Gap" --type concept --alias sg
novellum new "Poincare Lemma" --type proof --id lemma-poincare
novellum log new
```
> [!NOTE]
> Most of the flags are optional, and you can modify them in the actual `.tex`. Checkout the help for more assistance.

Open or create today's log note:

```sh
EDITOR="nvim" novellum today
```

Inspect and navigate:

```sh
novellum list
novellum show
novellum backlinks
novellum broken
novellum search poincare
```

> [!NOTE]
> Commands like `show`, `edit`, `links`, `backlinks`, and `stitch` now default to interactive note picking through `fzf` when you omit note IDs.
> If `fzf` is not installed, Novellum warns and falls back to the old non-interactive behavior.
> Use `--no-interactive` to disable that behavior explicitly.

Produce a stitched document and compile it:

```sh
novellum stitch spectral-gap lemma-poincare --title "Draft Notes"
novellum compile stitched
novellum open stitched
```

Or stitch the whole workspace:

```sh
novellum stitch --all --title "Whole Notebook"
novellum compile stitched
```

## Workspace Layout

`novellum init` creates a workspace like this:

```text
.novellum/
  config.toml
  index.json
  templates/
notes/
  concept/
  proof/
  paper/
  experiment/
  question/
  log/
  ref/
bibliography/
  references.bib
tex/
  workspace.tex
  novellum.sty
build/
```

Some notes:

* note files under `notes/` are the source of truth
* `.novellum/index.json` is a generated cache and can be rebuilt
* `tex/workspace.tex` is a normal LaTeX root for editor integration
* `bibliography/references.bib` is the shared bibliography file
* `build/` stores stitched output and compile artifacts

## Note Format

Here is what a note looks like:

```tex
% novellum:begin
% id: spectral-gap
% title: Spectral Gap
% type: concept
% created: 2026-04-03T00:00:00Z
% updated: 2026-04-03T00:00:00Z
% tags: analysis, operator-theory
% aliases: sg
% novellum:end

\section{Spectral Gap}

This connects to \nvlink[The Poincare Lemma]{lemma-poincare}.
We can still cite things normally with \cite{engel_nagel_2000}.
```

Important details:

* IDs resolve before aliases
* ambiguous aliases are treated as errors for direct lookup
* ambiguous aliases are reported as broken links in diagnostics
* only `\nvlink` is used for internal note graph edges

## Bibliography

`novellum` keeps citations standard. Use normal LaTeX citation commands like `\cite{key}` in note bodies.

The default workspace uses `natbib` with BibTeX rather than `biblatex` with `biber`. That choice is mostly pragmatic: it is simpler to get working on a lot of machines and makes the default compile workflow less annoying.

That means:

* VimTeX can still see a real TeX root
* citation completion can still use `bibliography/references.bib`
* notes stay readable as plain LaTeX fragments
* compilation works with `latexmk` plus a standard BibTeX recipe

## Usage

There are a few main workflows.

### Basic note workflow

Create notes:

```sh
novellum new "Heat Kernel Experiment" --type experiment --alias hk
novellum new "Operator Semigroup" --type concept
```

Inspect them:

```sh
novellum list
novellum show
novellum edit
novellum show hk --no-interactive
novellum edit operator-semigroup --no-interactive
```

### Graph workflow

Find outgoing links, backlinks, and diagnostics:

```sh
novellum links
novellum backlinks
novellum broken
```

### Logbook workflow

Create an explicit dated log:

```sh
novellum log new --date 2026-04-03
```

Or just open today's:

```sh
EDITOR="nvim" novellum today
```

### Document workflow

Stitch specific notes:

```sh
novellum stitch spectral-gap lemma-poincare --title "Analysis Draft"
novellum stitch --title "Choose Notes Interactively"
```

Stitch everything:

```sh
novellum stitch --all --title "Notebook Draft"
```

Compile either the workspace root or the stitched output:

```sh
novellum compile
novellum compile stitched
novellum compile build/drafts/custom.tex
```

Open the resulting PDFs:

```sh
novellum open
novellum open stitched
novellum open workspace
NOVELLUM_PDF_VIEWER="zathura" novellum open stitched
```

## Current Commands

* `novellum init`
* `novellum new`
* `novellum list`
* `novellum show`
* `novellum edit`
* `novellum links`
* `novellum backlinks`
* `novellum broken`
* `novellum search`
* `novellum stitch`
* `novellum compile`
* `novellum open`
* `novellum log new`
* `novellum today`

## Current State

Right now the project can already do the following:

* initialize a workspace
* create typed notes from templates
* create and open dated log notes
* index note links and backlinks
* search note metadata and body text
* generate stitched `.tex` output
* compile the workspace root or stitched files with `latexmk`
* open compiled PDFs with a configurable viewer
* rewrite stitched internal note links into clickable PDF hyperlinks
* default to `fzf`-based interactive note selection when it makes sense

The next obvious work is mostly polish and figure out how to make a neovim integration.
