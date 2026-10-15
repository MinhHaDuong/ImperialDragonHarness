# Backfilling a staging directory

A whole `docs/` folder is not the happy path repeated N times. Two things
change, and both are failure modes rather than conveniences.

**Dedup must be possible at all.** Every lookup reads the desktop client's
`zotero.sqlite`, afresh on each run (about 0.4 s for a 7,672-work library,
measured 2026-10-15). On a machine with no desktop client that file does not
exist, every lookup returns `verdict: "unchecked"`, and a backfill that reads "unchecked"
as "absent" re-imports the entire library. Run the backfill where the
desktop database lives; a clean negative then stays distinguishable from a
lookup that could not run:

```bash
zotero.py audit docs/ --out /tmp/audit.json
```

For projects with BibTeX, use `reconcile` to discover `.bib` files at the
repository root and one level below it, follow their `file=` paths, and report
both linked files and unlinked staging files. It uses the BibTeX metadata when
matching linked files. The command is **report-only**: it never injects or
attaches anything; rows whose work is present without a file come back in
`suggested_edits` (item key, file) for the author to attach by hand. It
uses `docs/` as the staging default only when no `.bib` exists. A `.bib` with no usable staging path yields `verdict: unchecked`, not
an empty clean report.

```bash
out=$(mktemp "${TMPDIR:-/tmp}/zotero-reconcile.XXXXXX.json")
status=0
zotero.py reconcile . --out "$out" || status=$?
echo "reconcile report: $out (exit $status)"
[ "$status" -eq 0 ]
```

Resolve any `errors` and inspect `ambiguous` rows before taking action. An
`absent` row is a proposal for a later, explicit import, not permission to
auto-inject it. Every early exit (nothing staged, no database) still writes
`--out` with the same report keys.

For an opted-in import, the project owner adds a root-level
`.zotero-reconcile.json` containing `{"apply": true, "user_id": "123456"}`,
where `user_id` is the account the local Zotero is signed in to (an optional
`collection` key files created items there). Then, with Zotero running, run
`reconcile . --apply`; no maintenance skill runs it for you. The script
locks the staging directories and the Zotero data directory (advisory locks
on the directories themselves, no lock files), re-reads `zotero.sqlite`, and
creates only absent PDFs with corroborated title/author metadata, through the
desktop connector. The re-read covers the destination library, so with a
group `collection` the duplicate check reads that group. Missing metadata, weak matches, ties, and discovery errors
remain visible in `deferred` or `errors`; they cannot become an automatic
write. Existing items are never edited: their fixes stay in
`suggested_edits`. The default invocation stays report-only.

Nothing is recorded between runs. The duplicate guard in `inject` is the
fresh read of the library plus a check of the batch against itself; use
`--force` only after inspecting a legitimate exception. While Zotero runs it
holds `zotero.sqlite` locked, so that read is the immutable snapshot, which
can miss the client's most recent saves (`read_mode: "immutable"` and a
`warning` in the output). A save that fails in transit stops the run; look
in Zotero before retrying, and check the *Duplicate Items* pane after a
retried sweep.

`audit` classifies every staged file into five verdicts, and the distinction
between the middle two decides what you do next:

| verdict | meaning | action |
|---|---|---|
| `identical` | this exact file is already stored (md5) | nothing |
| `work_present_with_file` | the work is in Zotero with a different copy | nothing; report it |
| `work_present_no_file` | the item exists, no file attached | `attach`, never `inject` |
| `ambiguous` | a weak hit — neither present nor absent | look at it |
| `absent` | not in the library | `inject` |

**`ambiguous` is a real answer, not a tuning failure.** Collapsing a weak hit
into one of its neighbours is expensive in both directions: called present, the
document is skipped and its full text never lands; called absent, a duplicate
item is minted. Over 289 files the strong verdicts agreed with a hand-built
resolver exactly — 100/100 `identical`, 169/169 `absent` — and every case where
the two differed came back `ambiguous`. That is the verdict earning its place:
it is where the judgment is needed, and it is a dozen files, not three hundred.

A title is matched as a **phrase, not a vocabulary**: the library title's words
must co-occur within a few consecutive lines *and* make up most of what those
lines contain. Scoring the whole document bag instead lets the five ordinary
words of "Systems of inequalities involving convex functions" match any paper
about linear inequalities — which filed a real Hoffman 1960 paper as a different
Hoffman paper, at `strong`.

**Content hash is the strongest key available** (`storageHash`, the md5
Zotero records for each stored file): it survives renaming, re-filing and
metadata drift, and it answers the question a staging directory actually
asks — *is this exact file already stored?* Prefer it over any title
comparison.

**`work_present_no_file` is repaired by attaching, not by `inject`.**
`inject` only ever creates items, so using it here mints a duplicate of a
work the library already holds. The connector cannot attach to an existing
item, so `attach` checks the item and the file and prints the by-hand step
(in Zotero: Add Attachment → Attach Stored Copy of File):

```bash
zotero.py attach --parent <itemKey> docs/Walley1991.pdf
```

Before trusting an audit's negatives, run it against a case you know is
positive — a guard whose "all clear" is indistinguishable from "I could not
look" is not a guard. `consulted` / `skipped` in every result exist for that.
