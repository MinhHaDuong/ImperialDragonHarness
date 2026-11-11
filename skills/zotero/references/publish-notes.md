# publish-notes: merged drafts become child notes

A reading note is drafted as an HTML file in a project's repository, reviewed
on a branch and merged. `publish-notes` then files it in Zotero as a child
note of the work it reads, through the local API only (author ruling
2026-11-11; the Web API is never used). From then on Zotero's note is the
record, and the author corrects it in Zotero's note editor.

```bash
"$IDH_ROOT/scripts/zotero.py" publish-notes --project <project> [--dry-run] \
    [--state-file PATH] [--library user|<groupID>] <draft.html>...
```

## What a draft must carry

- **The work's item key** in the draft's field table: the row whose first
  cell reads `zotero_item`, its second cell the key. The row is found by its
  cell text, whatever markup wraps it (`<th>`, `<td>`, a `<tbody>`, a `<p>`
  inside the cell), so a table the editor rewrote still reads. A draft with
  no such row is refused: the key is never guessed from a title or a file
  name.
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
| a tagged note with no record on this machine | — | `in sync` if its HTML equals the draft (recorded), else `refused` | none |
| several tagged notes | — | `refused` | none |

A refused note is reconciled by hand: carry Zotero's edits into the draft, or
the draft's into Zotero. Nothing is ever overwritten blind; the update itself
carries the note's version, so an edit made during the run is refused by
Zotero too.

`--dry-run` reads only and prints `would create`, `would update`, `in sync`,
`edited in zotero` or `refused`; it records nothing.

## The state file

After each write the note's key, its new version and the draft's sha256 are
recorded under `<project>/<slug>` in a JSON file outside git:
`$XDG_STATE_HOME/idh/zotero/publish-notes.json` (default
`~/.local/state/idh/zotero/publish-notes.json`), or `--state-file`. It holds
no credential and no note text. It is per machine: a note published from
another machine has no record here and is refused until reconciled. Writing
runs serialise on a lock of the file's directory.

## Output and exit status

JSON on stdout: `project`, `dry_run`, `state_file`, `zotero` (the URL, or
`unavailable` / `slow`) and `results`, one row per draft with `draft`,
`slug`, `tag`, `item`, `note`, `status` and, when refused, `reason`.

- 0: every row created, updated, in sync, edited in zotero, or would be.
- 1: a draft refused or not written.
- 75: Zotero unavailable. Nothing was published and nothing is in sync; a
  run with nothing to publish exits 0 instead. When Zotero goes away
  part-way, the rows done are kept, the write in flight is `unknown`, the
  rest `not attempted`.
- 74: Zotero slow (a read not finished in time).

The first write may open Zotero's key dialog (SKILL.md § Safety contract).
