# `novellum retag`

`retag` replaces the full tag list on a note.

Examples:

```sh
novellum retag spectral-gap --tag analysis --tag operator-theory
novellum retag
```

If you omit the note reference, Novellum can select a note interactively with
`fzf`. If you omit all `--tag` values, Novellum prompts for a comma-separated
tag list. Use `--no-interactive` for strict scripting behavior.
