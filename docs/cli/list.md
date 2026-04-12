# `novellum list`

`list` prints a compact table of notes with ID, type, title, link count, and
path.
You can also invoke it as `novellum ls`.

Examples:

```sh
novellum list
novellum list --type proof
novellum --json list
```

This is the plain inventory view for the workspace.

With `--json`, the command emits a payload containing the workspace root,
optional type filter, and a `notes` array. Each note includes:

* `id`
* `title`
* `type`
* `path`
* `created`
* `updated`
* `tags`
* `aliases`
* `link_count`
