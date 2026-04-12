# `novellum backlinks`

`backlinks` answers a simple question: who links to this note?

Example:

```sh
novellum backlinks lemma-poincare
novellum --json backlinks lemma-poincare --no-interactive
```

If a source note used a label in `\nvlink[Label]{target}`, the label is shown
too.

With `--json`, the payload includes the resolved note and a `backlinks` array
of inbound link records.
