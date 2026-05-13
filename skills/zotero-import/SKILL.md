---
name: zotero-import
description: Import one or more PDFs into Zotero. Extracts metadata from the document, resolves identifiers online when available, checks for duplicates in the local Zotero library, writes a combined RIS file, and hands it to xdg-open so the user's environment decides what to do with it.
disable-model-invocation: false
user-invocable: true
argument-hint: <pdf>... [--zotero-db PATH] [--no-attach] [--ris-out PATH]
---

# Zotero import

Build a single RIS file from one or more PDFs and hand it to `xdg-open`. The user's MIME associations decide whether it lands in Zotero or a text editor — both outcomes are acceptable. **Never** drive Zotero by other means.

## Happy path

1. `probe` each PDF with the helper script.
2. Read the extracted first/last-page text. Synthesize title, authors, year. Pick up DOI / ISBN / handle / arXiv ID surfaced by the script.
3. **If a strong identifier is present**, resolve it online (CrossRef for DOI, OpenLibrary for ISBN, arXiv API for arXiv ID) and prefer the canonical metadata returned.
4. **If no identifier is present**, search the web for `"<title>" <first author> <year>` to confirm the metadata before writing.
5. Run `match` against the Zotero DB using the *refined* title (probe's naïve match uses the often-garbage pdfinfo title — don't rely on it).
6. If duplicates exist, **warn the user and ask** before importing. Default is import-with-warning; remind to dedupe inside Zotero.
7. Translate the title to English. Put it in the **Short Title** field (RIS `ST`, which Zotero calls "Short Title" / abbreviated title).
8. `write` one combined RIS file alongside the first PDF.
9. `xdg-open` the RIS file. Stop. Let the user's environment do the rest.

## Helper script

`~/.claude/scripts/zotero-import.py` exposes:

- `probe <pdf>... [--zotero-db PATH]` — JSON to stdout. Fields per PDF: `pdfinfo`, `page_count`, `first_pages_text`, `last_pages_text`, `identifiers` (doi/isbn/handle/arxiv), `year_hint`, naive `zotero_matches`.
- `match [--title T] [--doi D] [--year Y] [--pdf P] [--zotero-db PATH]` — refined Zotero lookup using the title *you* extracted. Returns scored hits with attachment info and a `pdf_basename_match` flag.
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

After refined `match`, classify each PDF:

- **No hits** → import normally.
- **Hit with `pdf_basename_match: true`** → almost certainly already imported. Default: **skip**, tell the user, ask if they want to import anyway (e.g. to refresh metadata).
- **Hit with `score ≥ 90`, no attachment** → metadata already in Zotero but PDF not attached. Default: **import** so the PDF lands; warn that this will create a duplicate item the user should merge.
- **Hit with `60 ≤ score < 90`** → ambiguous. Show the candidate(s) to the user and ask.

Always remind the user that Zotero's *Duplicate Items* view (left panel) is the place to merge afterwards.

## Output to the user

End your turn with:

- The RIS file path.
- One line per PDF: title (orig) — `[type]` — `xdg-open` status — duplicate verdict.
- A reminder about Zotero deduplication if any duplicate-risk entry was imported.
