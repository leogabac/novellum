# Roadmap

This page tracks likely future implementations now that the core workflow is
starting to feel stable in real use.

The emphasis is on features that make a growing notebook safer to maintain.

## Near-Term Priorities

### Note Lifecycle Commands

Missing commands:

* `retag`
* alias add and remove helpers

The current CLI is strong at note creation and inspection, but weak at
controlled refactors after a note already exists.

Implemented so far:

* `rename`
* `move`
* `delete`

### Safer Graph Refactors

Changing a note ID should be able to update inbound `\nvlink{...}` references
across the workspace.

Today, `rename` already updates the canonical note ID and backing filename, but
it does not rewrite inbound links yet.

Likely command shape:

```sh
novellum rename old-id new-id --rewrite-links
```

Related ideas:

* dry-run mode
* refactor preview
* conflict detection before writes

### Richer Search and Filtering

Current search is intentionally simple. The next step is better query control.

Useful filters:

* `--tag`
* `--type`
* `--alias`
* `--linked-to`
* `--backlinked-by`
* `--updated-since`
* structured boolean filtering

### Maintenance Commands

The project already has indexing and diagnostics internally. It should expose
that more explicitly.

Likely additions:

* `novellum doctor`
* `novellum index rebuild`
* `novellum validate`

## Medium-Term Ideas

### Metadata-Aware Editing

Novellum should eventually support metadata changes without forcing raw manual
edits of the comment block.

Examples:

```sh
novellum meta set spectral-gap --title "Spectral Gap Notes"
novellum meta add spectral-gap --tag operator-theory
novellum meta add spectral-gap --alias sgap
```

### Machine-Readable Output

Commands like `list`, `search`, `links`, `backlinks`, and `broken` should
eventually gain `--json` support for shell pipelines, editor integrations, and
future TUI clients.
