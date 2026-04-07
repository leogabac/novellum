# `novellum edit`

`edit` resolves a note and opens it with the command in `$EDITOR`.

Example:

```sh
EDITOR="nvim -f" novellum edit spectral-gap
```

Novellum does not provide its own editor. This command resolves the note and
opens the corresponding file in the configured editor.

If `$EDITOR` is missing, the command errors clearly. If the note reference is
omitted, interactive selection is attempted unless disabled.
