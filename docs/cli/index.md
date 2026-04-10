# CLI

Novellum is a command-line note system because opening a full GUI just to jot
down a theorem fragment, one citation, and a short research-log sentence felt
like overkill.

This whole repo came from a very specific mood:

You are in the middle of reading something technical. You want normal LaTeX
files. You want links, but not a database-shaped application stack. You want a
daily log, but not a life-optimization dashboard.

So the answer, naturally, was to build a CLI.

Sensibly.

## How The CLI Thinks

Novellum does not treat notes as opaque blobs in an app sandbox. It assumes:

* notes are plain `.tex` files
* metadata lives in a comment block
* internal links are explicit `\nvlink{...}` commands
* the filesystem is still the source of truth

The CLI is mostly there to save you from repetitive maintenance and to give the
workspace a useful graph-shaped brain.

## Core Workflow

The usual rhythm is:

1. `novellum init` once.
2. `novellum new` whenever a new idea deserves a real file.
3. `novellum today` when you want the daily logbook loop.
4. `novellum links`, `backlinks`, `broken`, and `search` when the notebook stops fitting in your head.
   `graph` exports the resolved network as Mermaid when you want a broader view.
5. `novellum stitch`, `compile`, and `open` when the loose scraps need to become an actual draft.
   `stitch` can work from explicit references, category flags like `--concepts`, or `--all`.

## Interactive Selection

Several commands support interactive note picking when you omit a note
reference. If `fzf` is installed, Novellum will use it. If not, it falls back
to non-interactive behavior and tells you what went wrong.

Commands that can prompt this way include:

* `show`
* `edit`
* `links`
* `backlinks`
* `stitch`
* `select`

## Per-Command Reference

The command surface is now split into one page per command so it reads more
like an API manual and less like one very long reference page.

Start wherever you need:

* [init](init.md)
* [new](new.md)
* [list](list.md)
* [show](show.md)
* [edit](edit.md)
* [links](links.md)
* [backlinks](backlinks.md)
* [broken](broken.md)
* [search](search.md)
* [graph](graph.md)
* [stitch](stitch.md)
* [compile](compile.md)
* [open](open.md)
* [select](select.md)
* [log new](log-new.md)
* [today](today.md)
