# `novellum graph`

`graph` exports the resolved note graph as Mermaid `flowchart LR` text.

You can:

* export the whole workspace graph
* filter to one note type with `--type`
* write to stdout or a file with `--output`
* render directly with Mermaid CLI via `--render`

Examples:

```sh
novellum graph
novellum graph --output build/graph.mmd
novellum graph --type concept --output build/concepts.mmd
novellum graph --render svg
novellum graph --render png --output build/graph.png
```

Only uniquely resolved note-to-note links are included in the exported graph.
Direct rendering requires `mmdc` from Mermaid CLI to be installed on `PATH`.
