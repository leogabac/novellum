# novellum

CLI-first linked LaTeX notes for research logbooks.

## Direction

Novellum stays a CLI. The editor and richer UI layer can come later through a Neovim plugin and related integrations.

The storage model is intentionally LaTeX-friendly:

- notes are `.tex` files
- metadata lives in a leading LaTeX comment block
- links use a LaTeX-native macro: `\nvlink{note-id}` or `\nvlink[Label]{note-id}`
- each workspace is initialized with a local `.novellum/` directory

## Current Commands

- `novellum init`
- `novellum new`
- `novellum list`

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

## Next Steps

The scaffold is in place for:

- workspace initialization
- note creation from templates
- note listing
- metadata parsing
- LaTeX-native link extraction

See [PLAN.md](/home/holo/Documents/projects/novellum/PLAN.md) for the broader roadmap.
