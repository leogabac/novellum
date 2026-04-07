# `novellum log new`

`log new` creates a dated log note in `notes/log/`. Its ID format is stable:
`log-YYYY-MM-DD`.

Examples:

```sh
novellum log new
novellum log new --date 2026-04-03
novellum log new "Spent two hours fighting BibTeX again" --date 2026-04-03
```

Behavior details:

* `--date` must use `YYYY-MM-DD`
* the default title is the date
* tags include `log` and the date
* today's log gets aliases for the ISO date and `today`
* rerunning the command for the same date is idempotent

This is the explicit command for creating dated research log notes.
