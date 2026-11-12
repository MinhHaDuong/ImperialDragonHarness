# publish-notes: merged drafts become child notes

A reading note is drafted as an HTML file in a project's repository, reviewed
on a branch and merged. `publish-notes` then files it in Zotero as a child
note of the work it reads, through the local API only (author ruling
2026-11-11; the Web API is never used). From then on Zotero's note is the
record, and the author corrects it in Zotero's note editor.

```bash
"$IDH_ROOT/scripts/zotero.py" publish-notes --project <project> [--dry-run] \
    [--state-file PATH] [--library user|<groupID>] \
    [--collection "<key or path 'A / B'>"] <draft.html>...
```

## What a draft must carry

The draft is the reading-note template's file (`skills/reading-note/references/template.md`):
a YAML frontmatter block, then the HTML body. Only the body is published;
the frontmatter stays in the repository, and a change to it alone (a
`status` field, say) is no new version of the note.

- **The work's item key**: `zotero_item` in the frontmatter (top-level
  scalars only are read). Failing that, the body's field table: the row whose
  first cell reads `zotero_item`, found by its cell text whatever markup
  wraps it (`<th>`, `<td>`, a `<tbody>`, a `<p>` inside the cell), so a table
  the editor rewrote still reads. A draft with neither is refused: the key is
  never guessed from a title or a file name.
- **Its slug**: the file name without `.html`, no whitespace.

`--project` (one word, no `/`) and the slug make the note's tag,
`wiki:<project>/<slug>`. The tag, not the note's HTML, finds the note again:
the editor rewrites the HTML on its first save.

## What it does per draft

| Zotero holds under `zotero_item` | Draft since last publish | Status | Write |
|---|---|---|---|
| no note with the tag | — | `created` | a new child note, tagged |
| the tagged note, at the version recorded | unchanged | `in sync` | none |
| the tagged note, at the version recorded | changed | `updated` | the note's HTML, in place |
| the tagged note, at another version | unchanged | `edited in zotero` | none: the author's edit stands |
| the tagged note, at another version | changed | `refused` | none: "edited in Zotero since last publish" |
| a tagged note with no record on this machine naming its key, library and parent item | — | `in sync` if its HTML equals the draft's body (recorded), else `refused` | none |
| several tagged notes | — | `refused` | none |

A refused note is reconciled by hand: carry Zotero's edits into the draft, or
the draft's into Zotero. Nothing is ever overwritten blind; the update itself
carries the note's version, so an edit made during the run is refused by
Zotero too.

`--dry-run` reads only and prints `would create`, `would update`, `in sync`,
`edited in zotero` or `refused`; it records nothing.

## Filing the parent into a collection

`--collection` keeps a project's collection in step with its notes: the parent
item of every row not refused is added to that collection, given as a
collection key or as a path of names joined by `/` (`"Project / Sources"`), in
the library `--library` names. A string equal to a key is taken as that key; a
single name means a top-level collection; names match exactly, case included.
The collection is resolved once, before any write; an unknown or ambiguous one
stops the run (exit 1, nothing written). Filing only adds: the parent's other
collections stay, and a note `in sync` still repairs a parent missing from the
collection. Each row then carries `collection`: `would add` or `already in`
under `--dry-run`, `added` (read back after the write) or `already in`
otherwise. A refused row carries no `collection`. When filing fails after the
note was written, the row reads `not written` with the filing error as its
`reason`, although the note landed and the state file records it: a rerun
finds it `in sync` and retries the filing.

## The state file

After each write the note's key, its new version and the sha256 of the draft's body are
recorded under `<project>/<slug>` in a JSON file outside git:
`$XDG_STATE_HOME/idh/zotero/publish-notes.json` (default
`~/.local/state/idh/zotero/publish-notes.json`), or `--state-file`. It holds
no credential and no note text. It is per machine: a note published from
another machine has no record here and is refused until reconciled. Writing
runs serialise on a lock of the file's directory.

## Output and exit status

JSON on stdout: `project`, `dry_run`, `state_file`, `zotero` (the URL, or
`unavailable` / `slow`), `collection` (its key, with `--collection`) and `results`, one row per draft with `draft`,
`slug`, `tag`, `item`, `note`, `status` and, when refused, `reason`.

- 0: every row created, updated, in sync, edited in zotero, or would be.
- 1: a draft refused or not written.
- 75: Zotero unavailable. Nothing was published and nothing is in sync; a
  run with nothing to publish exits 0 instead. When Zotero goes away
  part-way, the rows done are kept, the write in flight is `unknown`, the
  rest `not attempted`.
- 74: Zotero slow (a read not finished in time).

The first write may open Zotero's key dialog (SKILL.md § Safety contract).

## pull-notes: the notes back as HTML

```bash
"$IDH_ROOT/scripts/zotero.py" pull-notes --project <project> \
    [--out-dir DIR] [--library user|<groupID>]
```

The read side, through the same local API and the same tag key
`wiki:<project>/<slug>`: a pull right after a publish reads what was
published, and a note edited in Zotero's editor since is read as edited. It
writes nothing to Zotero. The harness emits HTML and metadata only; any
`.qmd` envelope belongs to the consumer.

JSON on stdout: `project`, `zotero` and `results`, one row per note with
`slug`, `tag`, `item` (the parent's key), `note` (its key), `version`,
`date_modified`, `status: pulled` and `html`. With `--out-dir`, the HTML goes
to `DIR/<slug>.html` and the row carries `file` instead of `html`. Two notes
under one tag are both `ambiguous` (no HTML, nothing written, exit 1).

- 0: the project's notes, possibly none (`results: []` with Zotero up).
- 75: Zotero unavailable; the JSON holds no `results`, so an unreachable
  library is never read as an empty project. 74: Zotero slow.
- 1: a malformed `--project`, an unwritable `--out-dir`, or an ambiguous slug.
