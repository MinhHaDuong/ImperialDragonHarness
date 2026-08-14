---
name: zotero-import
description: Import one or more PDFs into Zotero — extract metadata, resolve identifiers online, dedupe against the local library, and inject items with their PDFs through the Zotero Web API (RIS file as fallback).
disable-model-invocation: false
user-invocable: true
argument-hint: <pdf>...
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

## Helper script

`~/.claude/scripts/zotero-import.py` exposes:

- `probe <pdf>... [--zotero-db PATH] [--library L]` — JSON to stdout. Fields per PDF: `pdfinfo`, `page_count`, `first_pages_text`, `last_pages_text`, `identifiers` (doi/isbn/handle/arxiv), `year_hint`, naive `zotero_matches` (same shape as `match` output, fed from the raw pdfinfo title).
- `match [--title T] [--doi D] [--isbn I] [--arxiv A] [--handle H] [--author FIRST-AUTHOR] [--year Y] [--pdf P] [--library L] [--zotero-db PATH]` — deduplication lookup using the metadata *you* refined. Consults its keys strongest first — file content hash (`storageHash`, needs `--pdf` on disk) → persistent identifier (DOI, ISBN, arXiv, handle) → attachment filename → (first author, year, normalised title) → title Jaccard as last resort — and stops at the first key that fires. Output: `matches` (each hit carries `why` = which key fired, `certainty` = exact/strong/weak, attachment info, `pdf_basename_match`), a `verdict` (`match` / `ambiguous` / `none` / `unchecked`), and `consulted`/`skipped` so "found nothing" and "could not look" stay distinguishable. Scope defaults to the **user library** (the inject destination); a group-library copy does not count as already present — pass `--library all` or a numeric libraryID to widen deliberately.
- `write --out <ris-path> --entries-json '<json>'` — writes the combined RIS. Each entry accepts: `type` (RIS code, default `JOUR`), `title`, `shortTitle`, `authors` (array; `"First Last"` is auto-converted to `"Last, First"`), `year`, `doi`, `isbn`, `url`, `journal`, `volume`, `issue`, `pages` (e.g. `"281-285"`), `numPages`, `publisher`, `language`, `abstract`, `pdf`, `attach_pdf` (bool).

Zotero DB discovery order: `--zotero-db` flag → `$ZOTERO_DATA_DIR/zotero.sqlite` → `~/Zotero/zotero.sqlite` → `~/data/Zotero/zotero.sqlite` → `~/Documents/Zotero/zotero.sqlite` → parsed `~/.zotero/zotero/profiles.ini`. The script opens the DB read-only via `?immutable=1` so it works while Zotero is running.

## Field-mapping rules

- **Title** in the document's original language (RIS `TI`).
- **Short Title** = English translation of the title (RIS `ST`). Generate it yourself if the document doesn't supply one.
- **Authors**: prefer canonical order from CrossRef/OpenLibrary when available; otherwise extract from the byline on page 1. Convert `"First Middle Last"` → `"Last, First Middle"` (the script does this automatically, but do it once if you're feeding the script the wrong way around).
- **Page count**: include `numPages` for every entry. For monograph-like types (BOOK, THES, RPRT, CHAP, MANSCPT) the script emits it as RIS `SP`; for everything else it lands as a `pages:N` keyword (Zotero has no per-type "total pages" RIS slot for journal articles).
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
