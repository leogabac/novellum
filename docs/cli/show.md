# `novellum show`

`show` prints one note's metadata and body. References can be canonical IDs or
aliases.

Examples:

```sh
novellum show spectral-gap
novellum show sg
novellum show
```

If you omit the reference and have `fzf` installed, Novellum can prompt you
interactively. Use `--no-interactive` if you want strict scripting behavior.

What it shows:

* ID
* title
* type
* path
* tags
* aliases
* link count
* body text
