# `novellum new`

`new` creates a note from the workspace template for a note type. If you do not
provide an ID, Novellum derives one from the title.

Useful options:

* `--type` or `-t`
* `--id`
* repeated `--tag`
* repeated `--alias`

Example:

```sh
novellum new "Spectral Gap" --type concept --alias sg --tag analysis
```

This is the main note-creation command for the workspace.

If the resolved ID already exists anywhere in the workspace, the command fails
instead of creating a naming conflict.
