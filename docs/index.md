# novellum

<div class="nv-hero">
  <img src="assets/logo.svg" alt="novellum logo">
  <p><strong>Novellum</strong> is a local-first CLI for linked LaTeX research notes with an archiver's soul. Provides just enough structure to stop your notebook from becoming a beautiful academic landfill.</p>
</div>

It is for people who want:

* plain-text notes
* a normal LaTeX workspace on disk
* Obsidian-style linking without surrendering to a proprietary note box
* stitched draft documents assembled from fragments
* a shell-first workflow that still respects editor tooling

Notes live as `.tex` fragments under `notes/`. Metadata lives in a LaTeX
comment block. Internal links use `\nvlink{...}`. Shared references stay in one
`bibliography/references.bib`. The filesystem remains the source of truth,
which means your notes are still just files instead of app fossils.

## Just... why?

This repo came from a very particular irritation.

I wanted a notebook for theorem scraps, proof fragments, reading notes, and lab
log entries. I wanted linking and graph navigation. I also wanted normal TeX
files, normal shell tools, normal editor integration, and had approximately zero
interest in migrating my research notes into an app that would like to become
my entire lifestyle.

So the project became:

* local first, because I can't afford to pay Google Drive.
* LaTeX native, i.e. no funny parsing tricks that could make the LaTeX compiler angry.
* graph aware, i.e. fancy words that Obsidian people like to use
* CLI driven, for pedantic terminal users like me
* mildly theatrical, because apparently I cannot resist putting a little lore into my tooling

... and my only personality for the next couple monts after release.

## What It Already Does

Today, novellum can:

* initialize a workspace
* create typed notes from templates
* create and open dated research log notes
* resolve note IDs and aliases
* show backlinks and broken links
* search across metadata and note body text
* stitch selected notes into a standalone LaTeX document
* compile workspace and stitched outputs with `latexmk`
* open compiled PDFs in a configurable viewer

## Documentation Map

New here and trying to get useful in ten minutes instead of two hours?

* [10-Minute Guide](getting-started/10-minute-guide.md)

Want the CLI explained properly instead of being handed a handful of verbs and a dream?

* [CLI Overview](cli/index.md)
* [Per-command reference](cli/init.md)

Want the future plans, including the things the current version is very obviously missing?

* [Roadmap](roadmap.md)
