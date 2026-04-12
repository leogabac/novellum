# `novellum show`

`show` prints one note's metadata and body. References can be canonical IDs or
aliases.

Examples:

```sh
novellum show spectral-gap
novellum show sg
novellum show
novellum --json show spectral-gap --no-interactive
```

If you omit the reference and have `fzf` installed, Novellum can prompt you
interactively with an inline dropdown picker. Use `--no-interactive` if you
want strict scripting behavior.

What it shows:

* ID
* title
* type
* path
* tags
* aliases
* link count
* body text

With `--json`, the command emits one `note` object containing the same metadata
plus the rendered body text.
