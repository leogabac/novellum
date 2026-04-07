# `novellum links`

`links` shows the local graph neighborhood for a note.

That includes:

* outbound links
* backlinks
* broken links originating from that note

Example:

```sh
novellum links spectral-gap
```

Use this when you want to inspect the local graph around one note.

Missing links are reported directly. Ambiguous aliases are shown with the set
of candidate note IDs.
