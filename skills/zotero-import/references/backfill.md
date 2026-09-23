# Backfilling a staging directory

A whole `docs/` folder is not the happy path repeated N times. Two things
change, and both are failure modes rather than conveniences.

**Dedup must be possible at all.** `probe` and `match` read the desktop
client's `zotero.sqlite`. On a machine with no desktop client that file does
not exist, every lookup returns `verdict: "unchecked"`, and a backfill that
reads "unchecked" as "absent" re-imports the entire library. Sync the Web API
index first — then `match` has a key to consult, and a clean negative stays
distinguishable from a lookup that could not run:

```bash
zotero-import.py sync-index          # ~1 min per 10k items; re-pulls every time
zotero-import.py audit docs/ --out /tmp/audit.json
```

For EDM projects with BibTeX, use `reconcile` to discover `.bib` files at the
repository root and one level below it, follow their `file=` paths, and report
both linked files and unlinked staging files. It uses the BibTeX metadata when
matching linked files. The command is **report-only**: it never injects or
attaches anything. It uses `docs/` as the staging default only when no `.bib`
exists. A `.bib` with no usable staging path yields `verdict: unchecked`, not
an empty clean report.

```bash
zotero-import.py reconcile . --out /tmp/zotero-reconcile.json
```

Resolve any `errors` and inspect `ambiguous` rows before taking action. An
`absent` row is a proposal for a later, explicit import, not permission to
auto-inject it. The command reuses the cached Web API index; `--refresh`
updates it first.

For unattended import, the project owner opts in with a root-level
`.zotero-reconcile.json` containing `{"apply": true, "user_id": "123456"}`
(an optional `collection` key files created items there). Then run
`reconcile . --apply`, or let `/molt` call it at the next maintenance. The
script locks staging and the user library, pulls a fresh index, and creates
only absent PDFs with corroborated title/author metadata. Missing metadata,
weak matches, ties, and discovery errors remain visible in `deferred` or
`errors`; they cannot become an automatic write. The default invocation stays
report-only. `inject` itself now consults the fresh index and append-only
file-md5 ledger; use `--force` only after inspecting a legitimate exception.
Successful creates enter the ledger before attachment upload so a failed
upload can resume under the same Zotero parent. Writes are sent in at most
50-item requests, and Zotero's `Backoff` / `Retry-After` headers are honored.

The 2026-09-23 tooling review found no existing unattended replacement for
this exact staging-to-library sweep. Zotero's native API supplies the actual
write and attachment protocol, but does not discover project BibTeX or stage
orphans. Better BibTeX is not installed in the checked Zotero profile and its
export mapping does not prove that a staged PDF was uploaded. The installed
plugin roster was empty at review time. `zotero-mcp` would still need the
same project discovery, duplicate guard, and durable replay state; adding it
would increase moving parts for this workflow. The local Zotero connector API
requires a running desktop client, whereas headless `/molt` must work without
one. The helper therefore reuses the existing Web API index and upload path.

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

**Content hash is the strongest key available**, and only the Web API index
carries it: it survives renaming, re-filing and metadata drift, and it answers
the question a staging directory actually asks — *is this exact file already
stored?* Prefer it over any title comparison.

**`work_present_no_file` is repaired with `attach`, not `inject`.** `inject`
only ever creates items, so using it here mints a duplicate of a work the
library already holds:

```bash
zotero-import.py attach --parent <itemKey> docs/Walley1991.pdf
```

Before trusting an audit's negatives, run it against a case you know is
positive — a guard whose "all clear" is indistinguishable from "I could not
look" is not a guard. `consulted` / `skipped` in every result exist for that.
