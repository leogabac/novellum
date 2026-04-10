# `novellum alias`

`alias` adds or removes aliases on an existing note.

Examples:

```sh
novellum alias add spectral-gap sgap
novellum alias remove spectral-gap sg
novellum alias add
novellum alias remove spectral-gap
```

If you omit the note reference, Novellum can select a note interactively with
`fzf`. If you omit the alias value, Novellum prompts for it. For `alias
remove`, the prompt offers the note's current aliases. Use `--no-interactive`
for strict scripting behavior.
