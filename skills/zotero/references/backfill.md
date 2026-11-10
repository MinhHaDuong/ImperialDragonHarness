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
entry's identifiers, title and type are what the lookup uses. A keyed file that no
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
| `unidentified` | no reliable identification: too little metadata, or a search by a title taken from the file (embedded Title or filename words), alone or with an identifier read from the pages, that finds nothing | give it a `.bib` entry or an `Author1999-TitleWords` name, then check again |
| `unchecked` | not looked up in full: the hash index was skipped, so a stored copy may have gone unseen | rerun when Zotero lists in time; never an import |


A title taken from the file itself, the PDF container's or the filename's, is
a search hint. A search on it may return a hit or candidates; a miss on it
alone is `unidentified`, never `absent`, even when `consulted` includes
`title`. Only a `.bib` title, or a consulted given identifier, lets a miss say
`absent`. A receipt's title is not given either: receipts do not mark it as
given or scraped, and `probe-url` stores the page's own title. The embedded
title is unreliable, not unusable: it is used, cautiously, and the code decides
nothing on it alone. On a row it leaves `unidentified`, the reading agent
judges from the title and the file; no pattern filters titles. Supply
bibliographic metadata before proposing an import.

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

**The lookup order: hash, identifiers, title.** `consulted` names each key
used.

1. **Hash** (`storageHash`): the staged file's md5 against the md5 Zotero 10
   reports for every stored attachment of the libraries `--library` names,
   listed once per run (Zotero has no search by md5). A hit is `identical`,
   whatever the file is called and whether or not it has a text layer. A
   hit under several items names the others in `also_matches`; a standalone
   attachment is reported by its attachment key with `standalone: true`; a
   copy under a trashed item does not count, and a linked file has no md5
   to match.
2. **Identifiers**: the `.bib` entry's `doi`, `isbn`, `arxiv` and `handle`,
   plus those its `url` states (an arxiv.org, hdl.handle.net or doi.org URL)
   and its `eprint` (arXiv, or a handle with `eprinttype = {hdl}`). When the
   entry gives none, the identifiers printed in the PDF's first and last
   pages, consulted as `doi (from text)` and the like. A page can print a
   cited work's DOI, so a text identifier alone never makes a file
   `absent` (a file reads `absent` only when a curated identifier or a
   given title, the `.bib` one, was searched too) and never
   lets `--apply --edit` attach it; its `suggested_edits` entry carries a
   `caution`.
3. **Title** (the `.bib` title, else the PDF's container Title, else the
   filename): a search that yields candidates, never a match. Only the
   `.bib` title is given; the other two are hints.

A hash miss alone never means `absent`: a file with nothing else to look it
up by is `unidentified`. When the attachment listing does not finish in time
or is refused, the run still completes on the identifiers and the title;
`hash_index` says `skipped`, each row's `skipped` says
`storageHash (index skipped: <why>)`, a file that would read `absent` reads
`unchecked`, the report's verdict is `unchecked`, `--apply` creates and
attaches nothing, and the exit is 74 for a slow listing, 1 for a refused
one. The listing costs about a minute on a library of 9,000 stored files
(Zotero hashes each file it lists); `find-work`, for one file, does not
list, and compares the md5 only with the works another key found.

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
`work_present_no_file`), fetch one DOI or ISBN at a time through the on-demand
DOIfetch helper:

```bash
"$IDH_ROOT/scripts/doifetch.sh" --doi <doi> --title <title>
"$IDH_ROOT/scripts/doifetch.sh" --isbn <isbn> --title <title>
```

The helper uses the pinned DOIfetch release. It tries
Crossref, Unpaywall, OpenAlex, HAL, ISTEX, and EZproxy first. For a DOI, it
then obtains the `shadow` extra and tries Sci-Hub; for an ISBN, it first resolves book-level DOIs via Crossref,
tries the open cascade for each, and then obtains the extra and tries LibGen. If ISBN lookup fails,
the helper reports that failure and stops: it cannot establish that the open
route was exhausted. A `source` in the result names the channel that actually
supplied a PDF. The helper stages the file in `docs/` (or the folder named by
`--output-dir`; it always passes one to DOIfetch) and records that source,
the DOI or ISBN it was given and the file's md5 in a receipt: the JSON line it
prints, appended to `<staging folder>/.receipts.jsonl`. `check-staging` and
`find-work --metadata <receipt>` read it back; nothing is recorded by hand.
`skipped` means the target file already existed; its origin is unknown, it
leaves no receipt, and must not be attributed to a source. Verify the file
belongs to the work before attaching.

On `success`, check the downloaded PDF, then file it with
`suggest-attachments --parent <itemKey> <file>` and add `--edit` after reading
the report. Exit 1 reports a failed fetch; exit 2 means invalid arguments; exit 3 means
ISBN lookup, HAL query setup, or another internal step failed before the
shadow phase. Exit 127 means `uvx` is absent, and 69 means the pinned DOIfetch or
its `shadow` extra could not be obtained. The open cascade is still attempted
before obtaining the extra. Name the failure; do not report an
unattempted source as unavailable. No per-project opt-in is required.

The helper's other modes forward their options to DOIfetch, adding
`--output-dir docs` when the caller gave none; its own upstream default
remains open and institutional sources only. Check the pinned
release with `"$IDH_ROOT/scripts/doifetch.sh" --version`.
