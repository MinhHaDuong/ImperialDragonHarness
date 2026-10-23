# Importing one or more PDFs or URLs

## Happy path

1. `extract-metadata` each PDF with the helper script (it never needs Zotero); for a URL, `probe-url.py` stages the document and extracts the same record shape (see URL intake below).
2. Read the extracted first/last-page text. Synthesize title, authors, year. Pick up DOI / ISBN / handle / arXiv ID surfaced by the script.
3. **If a strong identifier is present**, resolve it online (CrossRef for DOI, OpenLibrary for ISBN, arXiv API for arXiv ID) and prefer the canonical metadata returned.
4. **If no identifier is present**, search the web for `"<title>" <first author> <year>` to confirm the metadata before writing.
5. Run `find-work` for each PDF against the library, with its own extraction (`--metadata`, one PDF per file) and the *refined* title and identifiers as flags (the extracted title is the often-garbage pdfinfo one — don't rely on it). The flags are refused over a file of several PDFs.
6. If duplicates exist, **warn the user and ask** before importing; judge any title `candidates` yourself (see Duplicate handling). The default per verdict is in Duplicate handling.
7. Translate the title to English. Put it in the **Short Title** field (`shortTitle`, which Zotero calls "Short Title" / abbreviated title).
8. Write the entries JSON to a file next to the first item, then `create-items --entries-file` it; the helper launches Zotero if it is not running. When Zotero is unavailable (exit 75, `zotero: "unavailable"`), do nothing more: report the entries file for a later `create-items`.
9. Verify: the `create-items` output reports `status: "created"` per entry (plus `attachment` when `attach_pdf` was set). Each created entry carries its item `key`, plus `attachment_error` when Zotero refused the PDF, or `transport_error` when Zotero stopped answering after creating the item (the PDF may be missing or its attachment empty). Reads are live, so a `find-work` straight after an import sees the new item.

## URL intake

A URL is an input to `import`, not a separate flow (the former index-source
skill is absorbed here). The probe script
is the mechanical half; you are the brains: resolve identifiers, classify the
type, clean the metadata.

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

1. **Probe.** `python3 "$IDH_ROOT/skills/zotero/scripts/probe-url.py" <url>...`
   stages each document in `docs/` and prints a JSON record per URL:
   `staged_path`, `mime`, `page_count` (PDFs), `meta` (title/date/authors/
   publication/publisher), `identifiers` (doi/arxiv/isbn), `suggested_type`,
   and `full_pdf_url` when an HTML landing page advertises a downloadable PDF.
2. **Prefer the real document.** If `full_pdf_url` is present (institutional
   landing page → PDF), probe that too and attach the PDF, not the HTML overview.
3. Resolve identifiers and refine the metadata as for a PDF (identifier
   resolution below), then classify the type **with judgment** — don't
   rubber-stamp `suggested_type`. The lazy failure is calling everything a
   web page.
4. Continue on the shared path: `find-work` → `create-items` with
   `attach_pdf: true, pdf: <staged_path>` (works for HTML snapshots too), and
   optionally append a biblatex entry to the project `references.bib` so
   `@key` is citable now (provenance note = URL + "Document archivé dans
   Zotero").

### Type classification (the brains)

| Source nature | Entry `type` (Zotero item type) | Signals |
|---|---|---|
| Institutional / agency / think-tank PDF, official decision | `report` | PDF mime; `.org/.int/.gov` host; "report/paper/working paper" |
| Peer-reviewed article | `journalArticle` | DOI **and** a journal title (`citation_journal_title`) |
| News / analysis / blog (incl. specialist online outlets) | `webpage` | HTML; `og:type=article`; news/blog host |
| Newspaper / magazine piece | `newspaperArticle` / `magazineArticle` | only if you are confident; **biblatex `entrysubtype` does not survive Zotero import — prefer these types here, not `.bib`** |
| Research note (own `*.md`) | `document` | staged note, archived too |

Reports carry `numPages`. Don't invent a type the page doesn't support; when a
news site (e.g. Carbon Brief) is really just a web article, `webpage` is correct.

### Anti-bitrot / fetch failures

A `200` that is 4 KB of obfuscated JS is an anti-bot challenge, not the article
(seen on Premium Times). On `error` / a challenge stub, **find an alternate
source** that carries the same facts (another outlet, the publisher's own page,
a reputable roundup) and probe that — exactly as a human would. Note the
substitution in the entry.

## Creating the items

An entry's `type` is a Zotero item type (the column above; default `journalArticle`), checked against the running client's schema: a name Zotero does not know is refused. `create-items` maps the entries JSON onto Zotero item JSON (fields without a slot on the type, e.g. a DOI on a book, land in `extra`) and creates each item through Zotero's local API at `127.0.0.1:23119` (via pyzotero): the item is created in the destination library, in `--collection` when given, then the `attach_pdf` PDF is uploaded under it.

- **Zotero must answer.** When nothing answers, the helper launches Zotero (never in a container) and waits up to 90 s. If Zotero is still unavailable, nothing is saved and the output says so (`zotero: "unavailable"`, exit 75; a read Zotero does not finish in time is `zotero: "slow"`, exit 74). Exit 74 or 75 always means nothing was saved: when Zotero goes away after an entry was created, the run stops with exit 1 and the created rows. Enable Zotero Settings > Advanced > "Allow other applications on this computer to communicate with Zotero", or the helper fails naming that setting. Writing needs Zotero 10.0 or later and a local API key. On the first write without one, Zotero shows Allow / Always Allow / Deny: **tell the user to answer "Always Allow"** (the key is stored in `~/.config/keys/zotero-local.env`; the helper accepts no other answer, and a one-time "Allow" writes nothing). The helper asks before the first write and waits 120 s for the answer; with none, or a Deny, nothing is written.
- **Destination.** `--library` (the user library by default, or a numeric groupID such as an editable group) or `--collection KEY` (whose own library it uses). The item is created there directly; the Zotero window's selection plays no part. A read-only group cannot be a destination.
- **Duplicate guard.** Each entry is looked up in the **destination library** through Zotero's own search (DOI, ISBN, arXiv id and handle, then the title, then the content hash of each work found) just before it is saved, one entry at a time, so a later entry of the same batch finds the item an earlier one created; a copy in another library does not count. An identifier match (the item's own field: its DOI or ISBN field, a labelled `DOI:`/`ISBN:`/`arXiv:` line in Extra, its arXiv or handle URL; never the ISBN of a book section, conference paper, encyclopedia article or dictionary entry, which is its volume's) is refused as a duplicate; title candidates are refused too, listed under `candidates`, because the helper never judges a title: look at them, and pass `--force` only once you have judged the work distinct (two works can share a title). An entry with no identifier and no title of three words of three letters or more to search by is refused as well (an identifier that is blank or malformed, such as an ISBN with a bad check digit, counts as none). A batch also refuses a second entry that stores the same PDF file as an earlier one, since Zotero cannot search by md5. Nothing is recorded between runs: a re-run relies on those lookups, which see everything the client has saved.
- A save that fails in transit may still have reached Zotero, so the run stops there and marks the rest not attempted (`"not attempted after a failed save"`, or `"not attempted after Zotero stopped"` when Zotero went away during a PDF upload); inspect Zotero before retrying.
- `--dry-run` prints the item JSON and creates nothing; it needs Zotero running, because field placement uses the live schema. Use it to show the user what would be created when the metadata is uncertain.
- The call returns non-zero if any entry failed; the JSON output carries the per-entry error.

## Field-mapping rules

- **Title** in the document's original language (`title`).
- **Short Title** = English translation of the title (`shortTitle`). Generate it yourself if the document doesn't supply one.
- **Authors**: prefer canonical order from CrossRef/OpenLibrary when available; otherwise extract from the byline on page 1. Convert `"First Middle Last"` → `"Last, First Middle"` (the script does this automatically, but do it once if you're feeding the script the wrong way around). Institutions verbatim with a trailing comma so they aren't reordered.
- **Page count**: include `numPages` for every entry. Only `book`, `thesis` and `manuscript` have a real `numPages` field; every other type — reports included — gets it in Extra as `number-of-pages`.
- **Field placement is per item type**: a field the target type does not own is refused or dropped on save. `entry_to_zotero_item()` routes each value into the first slot field the type owns, read from the running Zotero's live schema (`/api/itemTypeFields`) — so `publisher` becomes `institution` on a report, `university` on a thesis, `journal` becomes `bookTitle` / `proceedingsTitle` / `series` / `seriesTitle` / `websiteTitle`, and even `year` is type-dependent (a patent has no `date` field, only `issueDate`). Anything with no home lands in Extra under its CSL name; nothing is dropped.
- **Every work type Zotero lists is accepted**, `patent`, `standard`, `case` and `statute` included: `title` lands in the type's own title field (`caseName`, `nameOfAct`, `subject`), Zotero's mapping. An unknown type is refused, never filed as something else.
- **A report needs four fields the generic ones don't cover**: `publisher` (→ `institution`), `place`, `number` (→ `reportNumber`), `genre` (→ `reportType`). Supply all four and the item is complete in one `create-items`.
- **PDF attachment**: pass `attach_pdf: true` plus the absolute `pdf` path. `create-items` uploads the file bytes through the local API, so Zotero stores a copy.
- **Filename is a fallback only** for title/year/authors. If you used the filename, say so in your summary so the user knows to spot-check.

## Identifier resolution

DOI → `https://api.crossref.org/works/{doi}` (JSON). Use `message.title[0]`, `message.author[*]`, `message.issued.date-parts[0][0]`, `message.container-title[0]`, `message.volume`, `message.issue`, `message.page`, `message.publisher`.

ISBN → `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`.

arXiv → `https://export.arxiv.org/api/query?id_list={id}` (Atom XML).

If the network call fails or returns no useful payload, fall back to the document-extracted metadata and note the fallback in your summary.

## Duplicate handling

After the refined `find-work`, classify each item by the `verdict`:

- **`verdict: "none"`** → import normally.
- **`verdict: "match"`** → already present in the destination library (`why` names the keys: `storageHash` first when the stored file is the same, then `doi`, `isbn`, `arxiv` or `handle`, the identifier the item's own field carries). Default: **skip** creation. If the hit has **no file** (`has_file: false`), attach to that existing item with `suggest-attachments --parent <itemKey> <file>`; inspect the report, then add `--edit` to store it (see `references/backfill.md`). Metadata changes use `suggest-edits`, not a duplicate item. Never use `--force` merely to supply a missing attachment.
- **`verdict: "ambiguous"`** (several matches tie, e.g. two records legitimately sharing one attachment md5) → show them to the user and ask. Never silently match, never silently skip.
- **`verdict: "candidates"`** (no identifier matched; Zotero's search returned works for the title, under `candidates`) → judge them yourself against the document: same work, another edition, or another work sharing the title. The helper never makes this call. Same work → skip or attach; distinct → import with `--force`; unsure → ask the user.
- **`verdict: "unchecked"`** → no key could be consulted (Zotero unavailable, or no usable metadata). Say so explicitly — this is not a clean negative.

Always remind the user that Zotero's *Duplicate Items* view (left panel) is the place to merge afterwards.

## Markdown research notes

Run these steps **sequential-blocking**: the note needs the source item keys,
and the storage receipt needs the completed upload. Archive sources at intake
and the finished note when produced; do not wait for manuscript submission.
A note is its own `document`, with its Markdown file stored under it. It does
not inherit the source work's DOI as its own identifier.

1. Stage the note in project-local `docs/`. Put the source Zotero library/key
   and the corpus `work_key` in its metadata (use `zotero:<library>:<key>` when
   there is no corpus id). For a paragraph note covering several works, list
   their keys. These are provenance links, not a new bibliography or a native
   Zotero relation created by the helper.
2. Prepare an entries file beside it, using only supported helper fields.
   Replace the example values with the real note author, date, title, absolute
   file path and source keys. `abstract` preserves the same provenance on the
   Document as `abstractNote`; `work_key` is not a supported top-level helper
   field. The historical `pdf` / `attach_pdf` names also accept Markdown:
   the helper uploads readable bytes and infers MIME from the filename.

   ```json
   [{"type":"document","title":"Reading note: Exact source title",
     "authors":["Actual note author"],"year":"2026-10-23",
     "abstract":"work_key: doi:10.example/source; source_items: user:ABCD1234",
     "pdf":"/absolute/project/docs/AuthorYear_Title.md","attach_pdf":true}]
   ```

3. Resolve `IDH_ROOT` as above, then look up the **note title and file**, not
   the source DOI. Judge title candidates as in Duplicate handling. An existing
   note Document with no file gets `suggest-attachments --edit`; a different
   saved version requires an explicit version decision, not a blind rerun.

   ```bash
   "$IDH_ROOT/scripts/zotero.py" find-work --type document \
     --title "Reading note: Exact source title" \
     --pdf /absolute/project/docs/AuthorYear_Title.md --library user
   "$IDH_ROOT/scripts/zotero.py" create-items \
     --entries-file /absolute/project/docs/note-entry.json --library user
   ```

4. Keep the creation output, then repeat that `find-work` command and retain
   its live JSON as the storage receipt. Require the intended Document key in
   `matches`, `why` containing `storageHash`, `has_file: true`, and a matching
   `attachment` with `linkMode: imported_file` and key/md5 under it; inspect the Document in the client to confirm its type
   and `abstractNote` provenance. Record library, source keys / `work_key`,
   note key, attachment key, hash and verification date in the run's existing
   output or handoff. `status: created` alone proves neither uploaded bytes
   nor the provenance link. An unavailable read, missing hash match or upload
   error leaves archiving pending; retain staging and inspect before retrying.

`check-staging` excludes Markdown. To reconcile produced notes, enumerate the
run's note paths (and staged `*.md` research notes in scope), repeat step 4 for
**each** current file, and list stored / pending / unverifiable with its
receipt or reason. Distinguish this note inventory from the document sweep;
a clean PDF report cannot certify that the notes are archived. A changed note
needs a fresh receipt for its current bytes. Keep this as archival evidence,
not a second bibliographic catalogue.
