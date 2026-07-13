---
name: index-source
description: Index/catalogue a document from a URL into Zotero with the right item type and clean metadata. Fetches the page, stages it locally, scrapes author/date/title/identifiers/pagination from meta tags (JSON-LD, citation_*, Dublin Core, OpenGraph) and DOI/arXiv APIs, classifies the Zotero type with judgment, dedupes, and hands a RIS + attachment to Zotero. URL sibling of zotero-import; implements the EDM workflow (docs/ staging → Zotero).
disable-model-invocation: false
user-invocable: true
argument-hint: <url>...
---

# index-source

Given one or more URLs, produce a correct Zotero entry for each — right item
type, real author/date/title, identifiers, page count — with the document
itself archived as an attachment. The probe script is the mechanical half; you
are the brains: resolve identifiers, classify the type, clean the metadata.

This is the URL sibling of `zotero-import` (which does PDFs). It follows the EDM
workflow: stage in `docs/`, store in Zotero; `docs/` and `.bib` are git-ignored
staging, never the home (see `rules/edm.md`).

## Happy path

1. **Probe.** `python3 ~/.claude/skills/index-source/scripts/probe-url.py <url>...`
   stages each document in `docs/` and prints a JSON record per URL:
   `staged_path`, `mime`, `page_count` (PDFs), `meta` (title/date/authors/
   publication/publisher), `identifiers` (doi/arxiv/isbn), `suggested_ris_type`,
   and `full_pdf_url` when an HTML landing page advertises a downloadable PDF.
2. **Prefer the real document.** If `full_pdf_url` is present (institutional
   landing page → PDF), probe that too and attach the PDF, not the HTML overview.
3. **Resolve identifiers.** If a DOI/arXiv/ISBN is present, fetch canonical
   metadata and prefer it over scraped tags — CrossRef `https://api.crossref.org/works/{doi}`,
   arXiv `https://export.arxiv.org/api/query?id_list={id}`, OpenLibrary for ISBN.
4. **Classify the type — with judgment** (don't rubber-stamp `suggested_ris_type`).
   See the table below. The lazy failure is calling everything a web page.
5. **Clean the metadata.** Real byline (personal authors `Last, First`;
   institutions verbatim with a trailing comma so they aren't reordered), full
   date, publication/publisher. Reports **get a page count** (`numPages`).
6. **Dedupe.** `python3 ~/.claude/scripts/zotero-import.py match --title "<refined title>" [--doi D]`
   — warn and ask before importing a likely duplicate. The user's own works are
   usually already in Zotero; check before adding.
7. **Write + import.** Build the entries JSON and
   `python3 ~/.claude/scripts/zotero-import.py write --out <file>.ris --entries-json '<json>'`,
   then `xdg-open` (or `setsid -f zotero`) the RIS. Attachments archive in Zotero
   (`attach_pdf: true`, `pdf: <staged_path>` — works for HTML snapshots too).
8. **Update the `.bib` (staging).** Optionally append a biblatex entry to the
   project `references.bib` so `@key` is citable now; provenance note = URL +
   "Document archivé dans Zotero".

## Type classification (the brains)

| Source nature | Zotero type | RIS code | Signals |
|---|---|---|---|
| Institutional / agency / think-tank PDF, official decision | Report | `RPRT` | PDF mime; `.org/.int/.gov` host; "report/paper/working paper" |
| Peer-reviewed article | Journal Article | `JOUR` | DOI **and** a journal title (`citation_journal_title`) |
| News / analysis / blog (incl. specialist online outlets) | Web Page | `WEB` | HTML; `og:type=article`; news/blog host |
| Newspaper / magazine piece | `NEWS` / `MGZN` | only if you are confident; **biblatex `entrysubtype` does not survive Zotero import — prefer RIS codes here, not `.bib`** |
| Research note (own `*.md`) | Document | `GEN` | staged note, archived too |

Reports carry `numPages`. Don't invent a type the page doesn't support; when a
news site (e.g. Carbon Brief) is really just a web article, `WEB` is correct.

## Anti-bitrot / fetch failures

A `200` that is 4 KB of obfuscated JS is an anti-bot challenge, not the article
(seen on Premium Times). On `error` / a challenge stub, **find an alternate
source** that carries the same facts (another outlet, the publisher's own page,
a reputable roundup) and probe that — exactly as a human would. Note the
substitution in the entry.

## Helper scripts

- `~/.claude/skills/index-source/scripts/probe-url.py <url>... [--staging-dir docs] [--timeout 60]` — fetch +
  stage + metadata. Stdlib only (no install). Uses `pdfinfo`/`pdftotext` for PDF
  page count and first-page text when available.
- `~/.claude/scripts/zotero-import.py` (global) — `match` (dedupe vs the Zotero
  DB) and `write` (RIS + `L1` attachment, `numPages`→page count on report types).

## Output to the user

End with: one line per URL — title — `[Zotero type]` — page count (reports) —
attachment archived? — duplicate verdict; the RIS path; and any source
substitution made for an unreachable original.
