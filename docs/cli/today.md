# `novellum today`

`today` opens today's log note in `$EDITOR`, creating it first if needed.

Example:

```sh
EDITOR="nvim -f" novellum today
```

If the file is missing, Novellum creates a note like `log-2026-04-07`, tags it
with `log` and the date, adds the aliases for the date and `today`, and opens
it immediately.

This command provides a quick daily log workflow by opening today's log note
immediately after creating it when necessary.
