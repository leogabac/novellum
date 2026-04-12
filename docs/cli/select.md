# `novellum select`

`select` is an interactive helper that prints chosen note IDs to stdout.

Example:

```sh
novellum select
novellum --json select
```

This is mostly useful for shell composition and future editor integrations. It
uses iterative `fzf` selection: pick one note, pick another, then stop when
done. The picker uses a bordered inline dropdown layout rather than taking over
the full terminal.

If `fzf` is unavailable, the command errors.

With `--json`, the selected note IDs are returned in a `selected_ids` array
instead of newline-delimited plain text.
