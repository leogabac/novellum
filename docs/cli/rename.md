# `novellum rename`

`rename` changes a note's canonical ID and renames the backing `.tex` file to
match.

Examples:

```sh
novellum rename spectral-gap spectral-gap-notes
novellum rename spectral-gap spectral-gap-notes --no-rewrite-links
novellum rename spectral-gap spectral-gap-notes --dry-run
novellum rename alpha beta
novellum rename
novellum rename spectral-gap
```

This updates the note metadata block and moves the file within its current note
type directory. If you omit the old ID, Novellum can select a note
interactively with `fzf`. If you omit the new ID, Novellum prompts for it.
Use `--no-interactive` for strict scripting behavior.

By default, `rename` also rewrites inbound `\nvlink{...}` references across
the workspace, including labeled links like `\nvlink[See this]{target}`.
Commented example lines stay untouched. Pass `--no-rewrite-links` if you only
want to rename the note itself.

If you want a preview first, pass `--dry-run`. Novellum will show the renamed
path and which notes would receive rewritten inbound links without changing any
files.

Typical interactive flow:

* run `novellum rename`
* pick the existing note with `fzf`
* enter the new canonical ID when prompted
