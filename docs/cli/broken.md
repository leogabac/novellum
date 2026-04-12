# `novellum broken`

`broken` scans the whole workspace for unresolved or ambiguous internal links.

Example:

```sh
novellum broken
novellum --json broken
```

Run it after manual refactors, imports, or other structural edits. If
everything is clean, Novellum reports that directly.

With `--json`, the command emits a `links` array of unresolved or ambiguous
references across the workspace.
