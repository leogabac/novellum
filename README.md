# novellum

CLI-first linked LaTeX notes for research logbooks.

## Direction

Novellum stays a CLI. The editor and richer UI layer can come later through a Neovim plugin and related integrations.

The storage model is intentionally LaTeX-friendly:

- notes are `.tex` files
- metadata lives in a leading LaTeX comment block
- links use a LaTeX-native macro: `\nvlink{note-id}` or `\nvlink[Label]{note-id}`
- each workspace is initialized with a local `.novellum/` directory
- each workspace also gets a normal LaTeX root in `tex/workspace.tex`
- the default bibliography lives at `bibliography/references.bib`

## Current Commands

- `novellum init`
- `novellum new`
- `novellum list`

## Workspace Layout

```text
.novellum/
  config.toml
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

`tex/workspace.tex` is the VimTeX-friendly root document. Notes remain fragments under `notes/`, while citations stay in the shared `bibliography/references.bib`.

## Note Format

```tex
% novellum:begin
% id: spectral-gap
% title: Spectral Gap
% type: concept
% created: 2026-04-02T00:00:00Z
% updated: 2026-04-02T00:00:00Z
% tags: analysis, operator-theory
% aliases: sg
% novellum:end

\section{Spectral Gap}

This note connects to \nvlink[The Poincare Lemma]{lemma-poincare}.
```

## Bibliography

Keep citations standard LaTeX. Notes should use normal commands such as `\cite{key}` and rely on the workspace root document to declare the bibliography.

That means:

- VimTeX can see a real TeX root
- citation completion can read `bibliography/references.bib`
- Novellum does not need a custom citation syntax

## Next Steps

The scaffold is in place for:

- workspace initialization
- note creation from templates
- note listing
- metadata parsing
- LaTeX-native link extraction

See [PLAN.md](/home/holo/Documents/projects/novellum/PLAN.md) for the broader roadmap.
