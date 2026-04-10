# `novellum move`

`move` changes a note's type and relocates the backing `.tex` file into the
matching note-type directory.

Examples:

```sh
novellum move spectral-gap proof
novellum move alpha ref
novellum move
novellum move spectral-gap
```

This updates the note metadata block and moves the file to the new category
directory. If you omit the old ID, Novellum can select a note interactively
with `fzf`. If you omit the destination type, Novellum prompts for it.
Use `--no-interactive` for strict scripting behavior.
