# `novellum rename`

`rename` changes a note's canonical ID and renames the backing `.tex` file to
match.

Examples:

```sh
novellum rename spectral-gap spectral-gap-notes
novellum rename alpha beta
novellum rename
novellum rename spectral-gap
```

This updates the note metadata block and moves the file within its current note
type directory. If you omit the old ID, Novellum can select a note
interactively with `fzf`. If you omit the new ID, Novellum prompts for it.
Use `--no-interactive` for strict scripting behavior. It does not rewrite
inbound `\nvlink{...}` references yet.
