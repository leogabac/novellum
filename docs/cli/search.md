# `novellum search`

`search` performs a case-insensitive substring search across note IDs, titles,
types, tags, aliases, and body text.

Examples:

```sh
novellum search poincare
novellum search semigroup
novellum --json search poincare
```

It is intentionally simple right now. There is no advanced query language yet,
just broad matching across the indexed note content.

With `--json`, the command emits the query string plus a `notes` array. Each
match includes note metadata and relative path information.
