# `novellum tag`

`tag` adds or removes tags on an existing note.

Examples:

```sh
novellum tag add spectral-gap analysis
novellum tag remove spectral-gap analysis
novellum tag add
novellum tag remove spectral-gap
```

If you omit the note reference, Novellum can select a note interactively with
`fzf`. If you omit the tag value, Novellum prompts for it. For `tag remove`,
the prompt offers the note's current tags. Use `--no-interactive` for strict
scripting behavior.
