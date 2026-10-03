# Importing one or more PDFs or URLs

## Happy path

1. `probe` each PDF with the helper script; for a URL, `probe-url.py` stages the document and extracts the same record shape (see URL intake below).
2. Read the extracted first/last-page text. Synthesize title, authors, year. Pick up DOI / ISBN / handle / arXiv ID surfaced by the script.
3. **If a strong identifier is present**, resolve it online (CrossRef for DOI, OpenLibrary for ISBN, arXiv API for arXiv ID) and prefer the canonical metadata returned.
4. **If no identifier is present**, search the web for `"<title>" <first author> <year>` to confirm the metadata before writing.
5. Run `match` against the Zotero DB using the *refined* title (probe's naïve match uses the often-garbage pdfinfo title — don't rely on it).
6. If duplicates exist, **warn the user and ask** before importing. Default is import-with-warning; remind to dedupe inside Zotero.
7. Translate the title to English. Put it in the **Short Title** field (`shortTitle`, which Zotero calls "Short Title" / abbreviated title).
8. `write` one combined RIS file alongside the first item — the durable import artifact, kept even when injection succeeds.
9. `inject` the same entries JSON. Report the returned item keys. On any per-entry error, or when no RW key resolves, fall back to `xdg-open` on the RIS file and say so.
10. Verify: the inject output lists one `itemKey` (plus `attachmentKey` when `attach_pdf` was set) per entry — read one item back if anything looks off. The local `zotero.sqlite` only reflects the change after the desktop client syncs; do not treat a stale local DB as a failed import.

## URL intake

A URL is an input to `import`, not a separate flow (the former index-source
skill is absorbed here, deprecated 2026-10-03, ticket 1018). The probe script
is the mechanical half; you are the brains: resolve identifiers, classify the
type, clean the metadata.

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

1. **Probe.** `python3 "$IDH_ROOT/skills/zotero/scripts/probe-url.py" <url>...`
   stages each document in `docs/` and prints a JSON record per URL:
   `staged_path`, `mime`, `page_count` (PDFs), `meta` (title/date/authors/
   publication/publisher), `identifiers` (doi/arxiv/isbn), `suggested_ris_type`,
   and `full_pdf_url` when an HTML landing page advertises a downloadable PDF.
2. **Prefer the real document.** If `full_pdf_url` is present (institutional
   landing page → PDF), probe that too and attach the PDF, not the HTML overview.
3. Resolve identifiers and refine the metadata as for a PDF (identifier
   resolution below), then classify the type **with judgment** — don't
   rubber-stamp `suggested_ris_type`. The lazy failure is calling everything a
   web page.
4. Continue on the shared path: `match` → `write` → `inject` with
   `attach_pdf: true, pdf: <staged_path>` (works for HTML snapshots too), and
   optionally append a biblatex entry to the project `references.bib` so
   `@key` is citable now (provenance note = URL + "Document archivé dans
   Zotero").

### Type classification (the brains)

| Source nature | Zotero type | RIS code | Signals |
|---|---|---|---|
| Institutional / agency / think-tank PDF, official decision | Report | `RPRT` | PDF mime; `.org/.int/.gov` host; "report/paper/working paper" |
| Peer-reviewed article | Journal Article | `JOUR` | DOI **and** a journal title (`citation_journal_title`) |
| News / analysis / blog (incl. specialist online outlets) | Web Page | `WEB` | HTML; `og:type=article`; news/blog host |
| Newspaper / magazine piece | `NEWS` / `MGZN` | only if you are confident; **biblatex `entrysubtype` does not survive Zotero import — prefer RIS codes here, not `.bib`** |
| Research note (own `*.md`) | Document | `GEN` | staged note, archived too |

Reports carry `numPages`. Don't invent a type the page doesn't support; when a
news site (e.g. Carbon Brief) is really just a web article, `WEB` is correct.

### Anti-bitrot / fetch failures

A `200` that is 4 KB of obfuscated JS is an anti-bot challenge, not the article
(seen on Premium Times). On `error` / a challenge stub, **find an alternate
source** that carries the same facts (another outlet, the publisher's own page,
a reputable roundup) and probe that — exactly as a human would. Note the
substitution in the entry.

## Injection

`inject` maps the same entries JSON onto Zotero item JSON (RIS type → Zotero `itemType`; fields without a slot on the type, e.g. a DOI on a book, land in `extra`), creates the items in one batch, then uploads each `attach_pdf` PDF as an `imported_file` attachment via Zotero's three-step upload contract.

- Credentials: `ZOTERO_RW_API_KEY` and `ZOTERO_USER_ID`, from the environment or `~/.config/keys/zotero.env`. Never inline a key into argv.
- `--collection KEY` files the new items under a collection.
- `--dry-run` prints the item JSON without touching the API — use it to show the user what would be created when the metadata is uncertain.
- The call returns non-zero if any entry failed; the JSON output carries the per-entry error.

## Field-mapping rules

- **Title** in the document's original language (RIS `TI`).
- **Short Title** = English translation of the title (RIS `ST`). Generate it yourself if the document doesn't supply one.
- **Authors**: prefer canonical order from CrossRef/OpenLibrary when available; otherwise extract from the byline on page 1. Convert `"First Middle Last"` → `"Last, First Middle"` (the script does this automatically, but do it once if you're feeding the script the wrong way around). Institutions verbatim with a trailing comma so they aren't reordered.
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

After refined `match`, classify each item by the `verdict`:

- **`verdict: "none"`** → import normally.
- **`verdict: "match"`** → already present in the destination library (`why` names the key: `storageHash`, `doi`, `isbn`, `arxiv`, `handle`, `filename`, `creator-year-title`). Default: **skip**, tell the user, ask if they want to import anyway (e.g. to refresh metadata). Exception: if the hit has **no attachment** and the key was metadata-level (not `storageHash`/`filename`), the PDF itself is missing from Zotero — default: **import** so the PDF lands, warning that this creates a duplicate item the user should merge.
- **`verdict: "ambiguous"`** (only title similarity fired, or several exact/strong candidates tie — e.g. two records legitimately sharing one attachment md5, ticket 0570) → show the candidate(s) to the user and ask. Never silently match, never silently skip.
- **`verdict: "unchecked"`** → no key could be consulted (no DB, or no usable metadata). Say so explicitly — this is not a clean negative.

Always remind the user that Zotero's *Duplicate Items* view (left panel) is the place to merge afterwards.
