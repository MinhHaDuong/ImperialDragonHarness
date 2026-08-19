---
name: zotero-import
description: "Import one or more PDFs into Zotero, or backfill a whole staging directory — extract metadata, resolve identifiers online, dedupe against the library (desktop database or a cached Web API index), and inject items with their PDFs through the Zotero Web API (RIS file as fallback)."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pdf>... | audit <dir>"
---

# Zotero import

Build the metadata for one or more PDFs, then `inject` items and attachments directly through the Zotero Web API (decided 2026-08-13; previously the flow ended at `xdg-open` on a RIS file and a human confirmation click). The RIS path remains the fallback when no read-write key is available or the user asks for a manual import.

## Happy path

1. `probe` each PDF with the helper script.
2. Read the extracted first/last-page text. Synthesize title, authors, year. Pick up DOI / ISBN / handle / arXiv ID surfaced by the script.
3. **If a strong identifier is present**, resolve it online (CrossRef for DOI, OpenLibrary for ISBN, arXiv API for arXiv ID) and prefer the canonical metadata returned.
4. **If no identifier is present**, search the web for `"<title>" <first author> <year>` to confirm the metadata before writing.
5. Run `match` against the Zotero DB using the *refined* title (probe's naïve match uses the often-garbage pdfinfo title — don't rely on it).
6. If duplicates exist, **warn the user and ask** before importing. Default is import-with-warning; remind to dedupe inside Zotero.
7. Translate the title to English. Put it in the **Short Title** field (`shortTitle`, which Zotero calls "Short Title" / abbreviated title).
8. `write` one combined RIS file alongside the first PDF — the durable import artifact, kept even when injection succeeds.
9. `inject` the same entries JSON. Report the returned item keys. On any per-entry error, or when no RW key resolves, fall back to `xdg-open` on the RIS file and say so.
10. Verify: the inject output lists one `itemKey` (plus `attachmentKey` when `attach_pdf` was set) per entry — read one item back if anything looks off. The local `zotero.sqlite` only reflects the change after the desktop client syncs; do not treat a stale local DB as a failed import.

## Injection

`inject` maps the same entries JSON onto Zotero item JSON (RIS type → Zotero `itemType`; fields without a slot on the type, e.g. a DOI on a book, land in `extra`), creates the items in one batch, then uploads each `attach_pdf` PDF as an `imported_file` attachment via Zotero's three-step upload contract.

- Credentials: `ZOTERO_RW_API_KEY` and `ZOTERO_USER_ID`, from the environment or `~/.config/keys/zotero.env`. Never inline a key into argv.
- `--collection KEY` files the new items under a collection.
- `--dry-run` prints the item JSON without touching the API — use it to show the user what would be created when the metadata is uncertain.
- The call returns non-zero if any entry failed; the JSON output carries the per-entry error.

## Enrichment — completing an item that already exists

`inject` creates; `enrich` completes. An item filed years ago under looser
habits, or scraped from a translator that dropped a field, keeps its gap
forever — `match` reports the item as present and the flow stops there. The
result is a system of record less complete than the staging folder it
supersedes, which is backwards. (Measured once: nine items in one library
held no DOI while the project `.bib` carried one for each.)

```bash
zotero-import.py enrich --item-key XRWZU4DZ \
  --expect-title "Optimum Utilization" --set DOI=10.2307/1907301
```

- **Verify the value before writing it, on the landing page, not the status
  code.** Copying a DOI from a `.bib` propagates whatever error is already
  there. Resolve it (CrossRef for the metadata, then follow the DOI and read
  where it lands) and confirm it names the work in hand.
- `--expect-title` is **required** and is the wrong-item guard: item keys are
  opaque, so a transposed key otherwise enriches an unrelated work silently.
  An item with no title is refused rather than written blind.
- A field already holding a **different** value is refused; `--overwrite`
  arbitrates. Correcting an empty field and replacing a curated one are not
  the same act. A field already holding the requested value is skipped, not
  rewritten — a no-op write bumps the version and shows as an edit in sync.
- Zotero field names are **case-sensitive** (`DOI`, not `doi`), and a field
  the item type does not own is refused with that reminder.
- The write is a `PATCH` of the named fields only, guarded by
  `If-Unmodified-Since-Version`: a concurrent edit fails with 412 instead of
  being silently overwritten. The item is then **read back** — a 204 says the
  request was accepted, not that the stored value is what you meant.
- `--jobs-file` takes `[{item_key, expect_title, set:{…}}]` for a batch.
  `--dry-run` reports the planned patch without writing.
- Exit code is non-zero when anything asked for did not happen, **a refusal
  included** — "wrote everything" and "declined every field" must not share
  an exit code.
## Backfilling a staging directory

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

## A scraped identifier is a hypothesis, not a finding

`find_identifier` regexes DOIs and arXiv ids out of page text, and page text
contains the reference list. The id it returns is frequently a **cited work's**,
not the document's own — and resolving it through CrossRef returns clean,
well-formed, confident, wrong metadata that nothing downstream questions. In a
158-PDF backfill this produced a Cottle memoir filed as an Albers paper on
Ronald Graham, a Parise–Ozdaglar item filed as Diaconis & Janson 2007, and a
Le Cadre item filed as Foti 2018.

So corroborate every resolved record against the document's own words before
accepting it:

```python
corroborate(resolved, first_pages_text)
# -> {"confidence": "corroborated" | "weak" | "contradicted" | "unchecked", ...}
```

`contradicted` means the resolved title and first author do not appear in the
document — discard the resolution and rebuild the metadata from the text, the
filename, and a web search. Cross-check against the project `.bib` where one
exists: it is curated by the author, so it corroborates, though it can be terse
or stale and does not replace reading the page.

The same discipline applies to the year: a `date` on the Zotero item can be a
reprint or translation date (Kantorovich 1942 recorded as 2004), so a year
mismatch alone is not evidence of a wrong match.

## Helper script

`~/.claude/scripts/zotero-import.py` exposes:

- `probe <pdf>... [--zotero-db PATH] [--library L]` — JSON to stdout. Fields per PDF: `pdfinfo`, `page_count`, `first_pages_text`, `last_pages_text`, `identifiers` (doi/isbn/handle/arxiv), `year_hint`, naive `zotero_matches` (same shape as `match` output, fed from the raw pdfinfo title).
- `match [--title T] [--doi D] [--isbn I] [--arxiv A] [--handle H] [--author FIRST-AUTHOR] [--year Y] [--pdf P] [--library L] [--zotero-db PATH]` — deduplication lookup using the metadata *you* refined. Consults its keys strongest first — file content hash (`storageHash`, needs `--pdf` on disk) → persistent identifier (DOI, ISBN, arXiv, handle) → attachment filename → (first author, year, normalised title) → title Jaccard as last resort — and stops at the first key that fires. Output: `matches` (each hit carries `why` = which key fired, `certainty` = exact/strong/weak, attachment info, `pdf_basename_match`), a `verdict` (`match` / `ambiguous` / `none` / `unchecked`), and `consulted`/`skipped` so "found nothing" and "could not look" stay distinguishable. Scope defaults to the **user library** (the inject destination); a group-library copy does not count as already present — pass `--library all` or a numeric libraryID to widen deliberately.
- `enrich (--item-key K --expect-title T --set FIELD=VALUE... | --jobs-file J) [--overwrite] [--dry-run]` — fills fields on **existing** items; see *Enrichment* above for the guards. Output: one row per item with `patch`, `refused`, `status` (`written` / `nothing to write` / `readback mismatch` / `failed`) and the post-write `version`.
- `sync-index [--reuse]` — pull the library (works + every attachment's md5) from the Web API into `~/.cache/zotero-import/index-<userid>.json`. Needs only a read key (`ZOTERO_API_KEY`, RW accepted). The bare command re-pulls unconditionally; `--reuse` is what enables the age check, reusing a cache younger than 24 h and re-pulling only past that.
- `audit <dir> [--out PATH] [--ext ...] [--refresh]` — reconcile a staging directory against the index. Per file: `verdict` (`identical` / `work_present_with_file` / `work_present_no_file` / `ambiguous` / `absent`), the matched `zotero_key`/`zotero_title`, `why` (which key fired), `certainty`, and `consulted`/`skipped`. Summary counts plus the action each verdict calls for on stdout; the full per-file report to `--out`.
- `attach --parent <itemKey> <file>...` — upload files onto an item that already exists. The repair for `work_present_no_file`; also how page-scan images or an HTML snapshot get filed under the work they belong to instead of becoming standalone items.
- `match ... [--source auto|api]` — `auto` (default) prefers the desktop database and falls back to the Web API index; `api` forces the index. Output shape and verdicts are the same either way, and both paths consult content hash, DOI, ISBN, arXiv, handle, attachment filename and (creator, year, title). One difference remains: the sqlite path has a final title-Jaccard sweep with no author constraint, which the index path does not — so a work whose recorded author differs from the one you supply can be found by the desktop cascade and missed by the index. `skipped` names every key that could not be used, so the gap shows in the output rather than passing as a clean negative.
- `write --out <ris-path> --entries-json '<json>'` — writes the combined RIS. Each entry accepts: `type` (RIS code, default `JOUR`), `title`, `shortTitle`, `authors` (array; `"First Last"` is auto-converted to `"Last, First"`), `year`, `doi`, `isbn`, `issn`, `url`, `journal` (container title, whatever the type), `volume`, `issue`, `pages` (e.g. `"281-285"`), `numPages`, `publisher`, `place`, `number`, `genre`, `conferenceName`, `edition`, `seriesNumber`, `language`, `abstract`, `pdf`, `attach_pdf` (bool). Any other key is **refused**, not ignored — a misspelt key that silently does nothing is the defect this guard exists to prevent.
  - `number` is the type's identifying number: report number, patent number, standard number.
  - `genre` is the type's kind-of-thing label: `"RAND Paper"` on a report, `"PhD thesis"` on a thesis, `"Working paper"` on a manuscript.
  - `place` is the city of publication (`"Santa Monica, CA"`).

Zotero DB discovery order: `--zotero-db` flag → `$ZOTERO_DATA_DIR/zotero.sqlite` → `~/Zotero/zotero.sqlite` → `~/data/Zotero/zotero.sqlite` → `~/Documents/Zotero/zotero.sqlite` → parsed `~/.zotero/zotero/profiles.ini`. The script opens the DB read-only via `?immutable=1` so it works while Zotero is running.

## Field-mapping rules

- **Title** in the document's original language (RIS `TI`).
- **Short Title** = English translation of the title (RIS `ST`). Generate it yourself if the document doesn't supply one.
- **Authors**: prefer canonical order from CrossRef/OpenLibrary when available; otherwise extract from the byline on page 1. Convert `"First Middle Last"` → `"Last, First Middle"` (the script does this automatically, but do it once if you're feeding the script the wrong way around).
- **Page count**: include `numPages` for every entry. On the RIS path (`write`), monograph-like types (BOOK, THES, RPRT, CHAP, MANSCPT) emit it as `SP` and everything else as a `pages:N` keyword (RIS has no per-type "total pages" slot for journal articles). On the API path (`inject`), only `book`, `thesis` and `manuscript` have a real `numPages` field; every other type — reports included — gets it in Extra as `number-of-pages`.
- **Field placement is per item type** on the `inject` path: posting a field the target type does not own is a hard 400 from the API. `entry_to_zotero_item()` routes each value through `ZOTERO_SLOT_FIELD` (a reduced snapshot of `api.zotero.org/schema`) — so `publisher` becomes `institution` on a report, `university` on a thesis, `journal` becomes `bookTitle` / `proceedingsTitle` / `series` / `seriesTitle` / `websiteTitle`, and even `year` is type-dependent (a patent has no `date` field, only `issueDate`). Anything with no home lands in Extra under its CSL name; nothing is dropped.
- **Every accepted RIS code reaches a real Zotero type.** `CPAPER`→conferencePaper, `GOVDOC`→report, `PAT`→patent, `STAND`→standard, `UNPB`→manuscript, `WEB`→webpage, following Zotero's own RIS translator. A code outside the accepted set still degrades to `document`, but logs a warning and records `Unmapped RIS type: <code>` in Extra — never silently.
- **A report needs four fields the generic ones don't cover**: `publisher` (→ `institution`), `place`, `number` (→ `reportNumber`), `genre` (→ `reportType`). Supply all four and the item is complete in one `inject`.
- **PDF attachment**: pass `attach_pdf: true` plus the absolute `pdf` path so Zotero picks it up via `L1`. The user has configured "Yes — let Zotero copy it": Zotero respects the user's *Linked Attachments* preference at import time.
- **Filename is a fallback only** for title/year/authors. If you used the filename, say so in your summary so the user knows to spot-check.

## Identifier resolution

DOI → `https://api.crossref.org/works/{doi}` (JSON). Use `message.title[0]`, `message.author[*]`, `message.issued.date-parts[0][0]`, `message.container-title[0]`, `message.volume`, `message.issue`, `message.page`, `message.publisher`.

ISBN → `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`.

arXiv → `https://export.arxiv.org/api/query?id_list={id}` (Atom XML).

If the network call fails or returns no useful payload, fall back to the document-extracted metadata and note the fallback in your summary.

## Duplicate handling

After refined `match`, classify each PDF by the `verdict`:

- **`verdict: "none"`** → import normally.
- **`verdict: "match"`** → already present in the destination library (`why` names the key: `storageHash`, `doi`, `isbn`, `arxiv`, `handle`, `filename`, `creator-year-title`). Default: **skip**, tell the user, ask if they want to import anyway (e.g. to refresh metadata). Exception: if the hit has **no attachment** and the key was metadata-level (not `storageHash`/`filename`), the PDF itself is missing from Zotero — default: **import** so the PDF lands, warning that this creates a duplicate item the user should merge.
- **`verdict: "ambiguous"`** (only title similarity fired, or several strong candidates tie) → show the candidate(s) to the user and ask. Never silently match, never silently skip.
- **`verdict: "unchecked"`** → no key could be consulted (no DB, or no usable metadata). Say so explicitly — this is not a clean negative.

Always remind the user that Zotero's *Duplicate Items* view (left panel) is the place to merge afterwards.

## Output to the user

End your turn with:

- One line per PDF: title (orig) — `[type]` — item key (or fallback/xdg-open status) — duplicate verdict.
- The RIS file path (artifact, and the fallback import route).
- A reminder about Zotero deduplication if any duplicate-risk entry was imported.
