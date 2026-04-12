# `novellum links`

`links` shows the local graph neighborhood for a note.

That includes:

* outbound links
* backlinks
* broken links originating from that note

Example:

```sh
novellum links spectral-gap
novellum --json links spectral-gap --no-interactive
```

Use this when you want to inspect the local graph around one note.

Missing links are reported directly. Ambiguous aliases are shown with the set
of candidate note IDs.

With `--json`, the payload includes:

* `note` for the resolved source note
* `outbound` for links originating from that note
* `backlinks` for inbound links
* `broken` for the unresolved or ambiguous subset
