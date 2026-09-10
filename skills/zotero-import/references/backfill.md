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
