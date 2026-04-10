# `novellum delete`

`delete` removes a note file from the workspace.

Examples:

```sh
novellum delete spectral-gap --yes
novellum delete
```

If you omit the note reference, Novellum can select a note interactively with
`fzf`. In interactive mode it asks for confirmation with the note ID, title,
type, and path before deleting. Use `--yes --no-interactive` for strict
scripting behavior.
