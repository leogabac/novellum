# `novellum init`

`init` creates the workspace skeleton. It is the command you run once before
adding notes to the workspace.

It creates:

* `.novellum/` for config, cache, and templates
* `notes/` with the default type directories
* `bibliography/references.bib`
* `tex/workspace.tex`
* `tex/novellum.sty`
* `build/`

Example:

```sh
novellum init my-notes
```

The command is idempotent. If the directory already looks like a Novellum
workspace, missing defaults are restored.
