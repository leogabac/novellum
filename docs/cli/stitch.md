# `novellum stitch`

`stitch` generates a standalone LaTeX document from selected notes.

You can:

* pass explicit note references
* use `--all`
* stitch whole categories such as `--concepts` or `--proofs`
* rely on interactive selection
* set a title
* choose a custom output path

Examples:

```sh
novellum stitch spectral-gap lemma-poincare --title "Analysis Draft"
novellum stitch --all --title "Whole Notebook"
novellum stitch --concepts --proofs --title "Theory Notes"
novellum stitch beta --concepts
novellum stitch --title "Pick Notes Interactively"
novellum stitch spectral-gap --output build/drafts/sg.tex
```

When stitched notes link to one another, Novellum rewrites those internal links
into clickable PDF hyperlinks in the generated document.

User preamble additions for stitched documents live in `tex/stitched-preamble.tex`.
For example:

```tex
\usepackage{physics}
```
