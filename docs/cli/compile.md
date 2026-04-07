# `novellum compile`

`compile` runs `latexmk` on the workspace root, the default stitched output, or
an explicit `.tex` file.

Supported targets:

* `workspace`
* `stitched`
* a relative `.tex` path
* an absolute `.tex` path

Examples:

```sh
novellum compile
novellum compile stitched
novellum compile build/drafts/sg.tex
```

If `latexmk` is missing, the command fails clearly.
