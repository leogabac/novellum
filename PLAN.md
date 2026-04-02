# Novellum Plan

## Vision

Novellum should be a Python CLI for maintaining a research logbook made of small linked LaTeX note fragments.

The closest mental model is:

- Obsidian-style linking and graph navigation
- Plain-text, local-first files
- LaTeX-first content instead of Markdown-first content
- A workflow optimized for research notes, derivations, references, experiments, and reusable snippets

The core idea is not "a terminal text editor". The core idea is "a structured note system with strong linking, search, and compilation support that happens to live in the CLI".

## Product Goal

Help a researcher do these things well:

- Capture a new idea quickly
- Split a large proof or derivation into reusable LaTeX fragments
- Link concepts, papers, experiments, and open questions together
- Search and traverse relationships between notes
- Compile selected note sets into a readable LaTeX document
- Maintain a timestamped research logbook over time

## Non-Goals For V1

These should stay out of the first version:

- Full-screen TUI editor
- Real-time graph visualization
- Multi-user sync
- Cloud storage
- Plugin system
- Rich PDF preview in-terminal
- Bibliography manager beyond minimal citation references

## User Model

The main user is a single researcher working on one or more projects locally.

Typical note types:

- `concept`: definitions, theorems, lemmas, intuition
- `proof`: proof fragments, derivations, algebraic manipulations
- `paper`: reading notes from papers
- `experiment`: computational results or test runs
- `question`: unresolved issues
- `log`: daily or session-based research journal entries
- `ref`: literature notes or citation-related notes

## Design Principles

- Local-first: everything lives in normal files and directories
- Plain text: no opaque database required for the source of truth
- Stable links: notes should be referenceable by IDs, aliases, and titles
- LaTeX-native: math content should feel first-class, not bolted on
- Scriptable: every operation should be CLI-friendly and composable
- Incremental: MVP should be useful before advanced UX exists

## Proposed Information Model

Each note should be a single text file with:

- A leading LaTeX comment block for metadata
- A body containing LaTeX content and inline links

Suggested file format:

```text
% novellum:begin
% id: theorem-spectral-gap
% title: Spectral Gap Bound
% type: concept
% tags: operator-theory, draft
% created: 2026-04-02T00:00:00Z
% updated: 2026-04-02T00:00:00Z
% aliases: gap bound
% novellum:end

\section{Spectral Gap Bound}

This connects to \nvlink{lemma-poincare} and \nvlink[Bakry-Emery]{paper-bakry-emery}.

\[
\lambda_1 \geq \cdots
\]
```

Notes:

- Metadata stays invisible to LaTeX because it is comment-based
- The body remains plain LaTeX-oriented text
- `links` should be derived automatically rather than manually maintained
- `id` should be the canonical stable identifier

## Proposed Repository Layout

```text
novellum/
  README.md
  PLAN.md
  pyproject.toml
  bibliography/
    references.bib
  tex/
    workspace.tex
    novellum.sty
  src/
    novellum/
      __init__.py
      cli.py
      config.py
      models.py
      parser.py
      storage.py
      index.py
      render.py
      commands/
        init.py
        new.py
        list.py
        show.py
        link.py
        search.py
        compile.py
        graph.py
  tests/
    test_parser.py
    test_storage.py
    test_links.py
    test_cli.py
```

## CLI Surface

### Foundation commands

- `novellum init`
  - initialize a workspace
- `novellum new`
  - create a note from a template
- `novellum list`
  - list notes with filters
- `novellum show <id>`
  - print or inspect a note
- `novellum edit <id>`
  - open note in `$EDITOR`

### Knowledge navigation

- `novellum links <id>`
  - show outbound and inbound links
- `novellum search <query>`
  - full-text and metadata search
- `novellum backlinks <id>`
  - show notes referencing a note
- `novellum graph <id>`
  - print a local adjacency view

### Research workflow

- `novellum log new`
  - create a dated research log entry
- `novellum today`
  - open or create today's log note
- `novellum stitch <id...>`
  - combine notes into a generated LaTeX document
- `novellum compile <target>`
  - compile a selected set into PDF via LaTeX

## Linking Syntax

Use a LaTeX-native link macro in the body:

- `\nvlink{note-id}`
- `\nvlink[Custom Label]{note-id}`

Possible future support:

- block anchors
- section references
- citations like `[@key]`

For V1, keep it simple:

- parse note IDs from `\nvlink`
- resolve them against known note IDs and aliases
- expose broken links in diagnostics

## Citations

Use standard LaTeX citation commands in note bodies, for example `\cite{key}`.

Bibliography management should be workspace-level:

- default shared bibliography: `bibliography/references.bib`
- real LaTeX root document: `tex/workspace.tex`
- helper package for Novellum macros: `tex/novellum.sty`

This keeps Novellum compatible with tools like VimTeX and biblatex, because the workspace looks like a normal LaTeX project rather than a custom note format with custom citation handling.

## Storage Strategy

Recommended workspace structure:

```text
.novellum/
  config.toml
  index.json
notes/
  concept/
  proof/
  paper/
  experiment/
  question/
  log/
bibliography/
  references.bib
tex/
  workspace.tex
  novellum.sty
build/
templates/
```

Notes:

- Source of truth is the note files under `notes/`
- `.novellum/index.json` is a generated cache, rebuildable at any time
- `build/` holds generated stitched `.tex` and compiled output
- `bibliography/references.bib` is the default shared citation database
- `tex/workspace.tex` acts as the default compilation root for editor tooling

## Architecture

### Core modules

- `models.py`
  - note metadata, note object, workspace config
- `parser.py`
  - comment metadata parsing and link extraction
- `storage.py`
  - file layout, note load/save, workspace discovery
- `index.py`
  - build note index, backlinks, broken-link checks
- `render.py`
  - produce stitched LaTeX outputs from note selections
- `cli.py`
  - top-level Typer or Click command registration

### Recommended dependencies

- standard library for the initial CLI
- `dataclasses` for models
- `pytest` for tests

Keep the dependency set small until real workflow pressure appears.

## MVP Definition

The first version is successful if it can do all of the following:

1. Initialize a workspace
2. Create typed notes from templates
3. Store notes as plain text with metadata
4. Parse `\nvlink`
5. Build an index of notes and backlinks
6. Search notes by text, title, tag, and type
7. Stitch selected notes into one LaTeX output
8. Open notes in the user's editor

That is enough to be useful for actual research work.

## Suggested Delivery Phases

### Phase 0: Project scaffold

- Set up `pyproject.toml`
- Choose packaging approach
- Add `src/` layout
- Add test setup
- Add formatter/linter config

### Phase 1: Workspace + note creation

- Implement `novellum init`
- Implement config file creation
- Implement note templates
- Implement `novellum new`
- Implement `novellum edit`

Deliverable:

- user can create and edit notes with stable IDs

### Phase 1.5: Navigation baseline

- Implement note resolution by ID and alias
- Build a workspace index for outbound links, backlinks, and broken links
- Implement `show`, `links`, and `search`
- Treat ambiguous aliases as errors instead of guessing

Deliverable:

- user can inspect, navigate, and search the note graph from the CLI

### Phase 2: Parsing + indexing

- Parse note bodies and metadata blocks
- Extract links from body
- Build workspace index
- Implement `list`, `show`, `links`, `backlinks`
- Report broken links

Deliverable:

- user can navigate a linked note graph

### Phase 3: Search

- Implement full-text scan
- Filter by tags, type, title
- Add output formatting with `rich`

Deliverable:

- user can find notes quickly

### Phase 4: Research logbook workflow

- Implement `log new`
- Implement `today`
- Add templates for session notes
- Support linking logs to concept/proof/paper notes

Deliverable:

- user can maintain a day-by-day research journal

### Phase 5: Stitch + compile

- Implement note selection rules
- Generate stitched `.tex`
- Optionally compile with `pdflatex` or `latexmk`
- Add dependency diagnostics when LaTeX tooling is missing

Deliverable:

- user can turn note fragments into a draft document

## First Technical Decisions

These are the decisions I would make unless later constraints change:

- Use Python 3.12+
- Use `src/` layout
- Use `typer` for CLI
- Use LaTeX comment metadata blocks
- Use file-based storage, not SQLite, for V1
- Use deterministic note IDs generated from titles unless explicitly provided
- Use `templates/` for note boilerplates
- Use rebuildable JSON index cache

## Risks

### Risk 1: LaTeX fragment composition gets messy

Why:

- Fragments may have conflicting preambles, macros, environments, or labels

Mitigation:

- keep note bodies fragment-friendly
- separate document preamble from note content
- define a stitch pipeline with a controlled wrapper template

### Risk 2: Linking syntax conflicts with LaTeX

Why:

- bracket-heavy syntax can interact poorly with some LaTeX writing styles

Mitigation:

- keep `[[...]]` links as plain text markers
- parse them before any compile pipeline
- optionally strip or transform links during rendering

### Risk 3: Search/index performance on larger note sets

Why:

- repeated full scans will slow down as the workspace grows

Mitigation:

- start with full scan
- cache parsed metadata in `.novellum/index.json`
- only optimize after real usage demands it

## Open Questions

These do not block the scaffold, but they matter soon:

- Should note bodies be pure LaTeX, or a hybrid format with light markup plus LaTeX blocks?
- Should note IDs be human-readable slugs only, or UUID-backed with slugs as aliases?
- Should stitched output preserve original note order, graph order, or explicit user order?
- How much bibliography support is needed in V1?
- Do you eventually want a TUI, or should this remain a pure command CLI?

## Recommended Next Session

When we continue, the highest-value next step is:

1. Create the Python project scaffold
2. Add `novellum init`, `novellum new`, and `novellum list`
3. Define the note file format in code
4. Add tests around parsing and note creation

If we do only that, we will have the base needed for every later feature.
