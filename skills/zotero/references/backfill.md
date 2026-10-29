# Backfilling a staging directory

A whole `docs/` folder is not the happy path repeated N times. Two things
change, and both are failure modes rather than conveniences.

**Dedup must be possible at all.** Every lookup asks the running Zotero's
own search, through its local API, live, per file; no lookup reads the whole
library. When Zotero is not
running the helper launches it; in a container, or when the launch fails,
the command does nothing and reports Zotero unavailable. A backfill that read
"could not look" as "absent" would re-import the entire library, so run it
on the machine where Zotero lives; a clean negative then stays
distinguishable from a lookup that could not run:

`check-staging` has two input modes. With `--dir`, it checks every staging
file under one directory of the repository, BibTeX or not:

```bash
"$IDH_ROOT/scripts/zotero.py" check-staging . --dir docs --out /tmp/staging.json
```

By default, it discovers `.bib` files at the repository root and one level
below it, follows their `file=` paths, and reports both linked files and
unlinked staging files. It uses the BibTeX metadata when matching linked
files: a `.bib` entry type of a part of a volume (`@incollection`,
`@inbook`, `@bookinbook`, `@inproceedings` and the like) is never looked up
by its ISBN, which is the volume's, and neither is a type the helper does
not map (`@misc`, `@suppperiodical`, a typo): it fails closed to the other
identifiers and the title. The command is **report-only by default**: without
`--apply` it never creates or attaches anything; rows whose work is present without a file come back in
`suggested_edits` (item key, file), which `--apply --edit` stores. It
uses `docs/` as the staging default only when no `.bib` exists. A `.bib` with no usable staging path yields `verdict: unchecked`, not
an empty clean report.

A project whose bibliography sits deeper, or whose staged files are named by
BibTeX key (`michaelowa2011.pdf`: no title words to look up), names it with
`--bib PATH` (repeatable) or a `bib_paths` list in `.zotero-reconcile.json`;
the default discovery still runs beside it. Under `--dir`, a named `.bib`
describes the files its `file=` fields link inside that directory, and the
entry's title, DOI and type are what the lookup uses. A keyed file that no
`.bib` describes stays `unidentified`; it is never guessed from its name.
`--skip-underscore-dirs` leaves out files below a directory whose name
starts with `_` (`_superseded/`); without it every directory is checked.
`check-staging` reads only `.pdf .html .htm .jpg .jpeg .png .djvu .epub`, linked
or not; a `.md` file is never a row of its report. The reconcile staging rule in
`rules/zotero.md` still covers `*.md` notes. Reconcile those separately with
the per-note inventory and live hash receipts in `references/import.md`,
section Markdown research notes. Report both scopes before claiming all
sources and notes archived.

```bash
"$IDH_ROOT/scripts/zotero.py" check-staging . --dir docs/articles \
  --bib deliverables/_shared/bibliography/main.bib --skip-underscore-dirs
```

```bash
out=$(mktemp "${TMPDIR:-/tmp}/zotero-staging.XXXXXX.json")
status=0
"$IDH_ROOT/scripts/zotero.py" check-staging . --out "$out" || status=$?
echo "check-staging report: $out (exit $status)"
[ "$status" -eq 0 ]
```

Resolve any `errors` and judge the `candidates` rows before taking action. An
`absent` row is a proposal for a later, explicit import, not permission to
create it automatically. Every early exit (nothing staged, Zotero unavailable) still
writes `--out` with the same report keys. Zotero unavailable is a clean
no-op: verdict `zotero_unavailable`, exit 0, nothing compared or created (exit 1 if discovery found errors, which stay listed; when discovery found errors and no file, the verdict is `unchecked` and Zotero is not asked).

For an opted-in import, the project owner adds a root-level
`.zotero-reconcile.json` containing `{"apply": true, "user_id": "123456"}`,
where `user_id` is the account the local Zotero is signed in to (an optional
`collection` key files created items there). Then run `check-staging . --apply`;
no maintenance skill runs it for you. The script locks the staging
directories and the user's runtime directory, or the home directory when
`XDG_RUNTIME_DIR` is unset (advisory locks on the directories themselves, no
lock files, given up after 10 min rather than hang), looks every file up again, live, and
creates only the absent PDFs a `.bib` entry describes with a title, an author
and a year, through the
local API (it needs Zotero 10.0 or later and the local API key; see
`references/helper-script.md`). The second lookup covers the destination library, so with a
group `collection` the duplicate check searches that group. A read Zotero does
not finish in time, at any step, is verdict `zotero_slow` with exit 74, never
the clean no-op of `zotero_unavailable`. An orphan file however complete its
pdfinfo (page text and pdfinfo are where a cited work's metadata slips in),
title candidates, ties, and discovery errors
remain visible in `deferred`, the rows or `errors`; they cannot become an automatic
write. Existing items are edited only with `--apply --edit`, which stores each
staged file under the one existing item that lacks it (a tie is left for the
author; `--edit` without `--apply` is an error). Without `--edit` their fixes
stay in `suggested_edits`. The default invocation stays report-only.

Nothing is recorded between runs. The duplicate guard in `create-items` is a
live lookup in the destination library just before each entry is saved, one
at a time, so the batch is checked against itself too; use `--force` only after inspecting a legitimate exception. A save
that fails in transit stops the run; the next run's read sees the item if it
was created.

`check-staging` classifies every staged file into six verdicts, and the distinction
between `work_present_with_file` and `work_present_no_file` decides what you do next:

| verdict | meaning | action |
|---|---|---|
| `identical` | this exact file is already stored (md5) | nothing |
| `work_present_with_file` | the work is in Zotero with a different copy | nothing; report it |
| `work_present_no_file` | the item exists, no file attached | `suggest-attachments`, never `create-items` |
| `candidates` | no identifier matched; Zotero's search found works with the title | judge them: same work, or another |
| `absent` | looked up, not in the library | `create-items` |
| `unidentified` | nothing to look it up by: no identifier, no title of three words of three letters or more | give it a `.bib` entry or an `Author1999-TitleWords` name, then check again |

**`candidates` is a real answer, not a tuning failure.** The helper asserts
a match only on an exact identifier (DOI, ISBN, arXiv id or handle equal to
the item's own field) or on the stored file's md5; a title is never one, and
neither is the ISBN of a part of a volume (a book section, conference paper,
encyclopedia article or dictionary entry), which identifies the volume. Collapsing
candidates into one of their neighbours is expensive in both directions:
called present, the document is skipped and its full text never lands;
called absent, a duplicate item is minted. Five ordinary words such as
"Systems of inequalities involving convex functions" once filed a real
Hoffman 1960 paper as a different Hoffman paper; a candidate list puts that
call in front of the reader instead.

**Content hash is the strongest key available** (`storageHash`, the md5
Zotero 10 reports for each stored file): it survives renaming, re-filing and
metadata drift, and it answers the question a staging directory actually
asks — *is this exact file already stored?* Zotero has no search by md5, so
the hash is compared with the files of each work another key found: a stored
copy under a work nothing else finds goes unseen, and a file with nothing to
look it up by is `unidentified`, never `absent`.

**`work_present_no_file` is repaired by attaching, not by `create-items`.**
`create-items` only ever creates items, so using it here mints a duplicate of a
work the library already holds. `suggest-attachments` checks the item and the file and
reports the attachment; with `--edit` it stores a copy of the file under the
item through the local API:

```bash
"$IDH_ROOT/scripts/zotero.py" suggest-attachments --parent <itemKey> docs/Walley1991.pdf          # report
"$IDH_ROOT/scripts/zotero.py" suggest-attachments --parent <itemKey> docs/Walley1991.pdf --edit   # store
```

Before trusting a check's negatives, run it against a case you know is
positive — a guard whose "all clear" is indistinguishable from "I could not
look" is not a guard. `consulted` / `skipped` in every result exist for that.

## Fetching missing fulltexts

For a work a staging or cited-works check reports without a stored file (verdict
`work_present_no_file`), fetch it with DOIfetch. The helper runs it on demand at
a pinned ref through `uvx`; nothing is installed, and uv caches it after the first run:

```bash
"$IDH_ROOT/scripts/doifetch.sh" --doi <doi> --title <title>
```

Pass no `--source`. The default list is open and institutional only (Crossref, Unpaywall,
HAL, ISTEX, EZproxy). File each downloaded PDF with
`suggest-attachments --parent <itemKey> <file>`, and add `--edit` after reading
the report. Never pass `--source scihub` or `--source libgen`: a source outside the
default list is the author's own manual, per-user choice, never the harness's.
The prerequisites are `uv` and the network. When the helper exits 127 (no `uvx`)
or its first run cannot download DOIfetch, say which and stop; do not fetch another way.
