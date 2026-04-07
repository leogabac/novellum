# `novellum open`

`open` opens a compiled PDF in a viewer. It can resolve from the stitched
target, the workspace root, a `.tex` path, or a direct `.pdf` path.

Viewer resolution order:

1. `NOVELLUM_PDF_VIEWER`
2. `PDF_VIEWER`
3. `zathura`
4. `xdg-open`
5. `open`

Examples:

```sh
novellum open
novellum open stitched
novellum open workspace
NOVELLUM_PDF_VIEWER="zathura" novellum open stitched
```

It assumes the PDF already exists. The command does not compile first.
