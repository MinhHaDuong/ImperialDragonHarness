---
metadata:
  category: research
name: zotero
description: "Import PDFs or URLs into Zotero, suggest edits or attachments to existing items, check staged files against the library, or report duplicate files: extract metadata, resolve identifiers, create items with PDFs through the running Zotero's local API."
disable-model-invocation: false
user-invocable: true
argument-hint: "import <pdf-or-url>... | suggest-edits | check-staging [<repo>] [--dir <dir>] | report-duplicates | suggest-attachments"
---

Discipline: `rules/zotero.md` — Zotero is the system of record, `docs/` and `.bib` are git-ignored staging. Read it before working outside the verb files. A cited page number is read on the page, never interpolated from an extraction (the rule carries the discipline).

# Zotero

One skill, verbs as arguments: the verb surface mirrors the backend
subcommands of the `zotero.py` helper. Narrowness is the domain, not the verb
count (harness precedent: the `reviewers` skill). A URL is an input to
`import`, not a separate verb or skill.

## Verbs

A run uses exactly one verb. **Read the verb's file before acting.**

| verb | does | file |
|---|---|---|
| `import` | one or more PDFs or URLs → new items with attachments | `references/import.md` |
| `suggest-edits` | report missing fields on items that already exist; write them only with `--edit` | `references/enrichment.md` |
| `check-staging` | compare staged files with the library — the files a repository's `.bib` links, or every staging file under `--dir` — and report; `--apply` creates absent items, `--apply --edit` also stores files under existing items | `references/backfill.md` |
| `report-duplicates` | hash-dedup JSON report, library against itself | `docs/zotero-report-duplicates.md` |
| `suggest-attachments` | file a document onto an item that already exists (reports by default; stores it with `--edit`) | `references/backfill.md` |

The former three modes dissolve into this surface: `import` and enrichment
map to the `import` and `suggest-edits` verbs, and the backfill mode is
`check-staging` — a staging sweep is not the import happy path repeated N
times, which is why `references/backfill.md` stays its reference. The former
index-source skill (URL intake) is absorbed into `import`: a URL is one more
input, probed by the skill's own `probe-url.py` script.

`extract-metadata`, `find-work` and `create-items` are the plumbing of
`import`, not user verbs: `extract-metadata` reads what a PDF says about
itself and never contacts Zotero, `find-work` looks the work up in the
library through the local API only (it takes `extract-metadata`'s output, and
the refined metadata as flags), and `create-items` creates the items through
the same API. `references/helper-script.md` documents every subcommand and
the guarantees of its output (`matches` / `candidates` / `why` /
`consulted` / `skipped`).

Inside `import`: extract-metadata → find-work → create-items.
`extract-metadata` (or `probe-url.py` for URLs) extracts, `find-work` dedupes
against a live read of the library, and `create-items` creates the items
through the Zotero local API. `references/import.md` carries the full
contract.

## Safety contract

The helper is local-only and stateless. Every library read goes through the
running Zotero's local API (`127.0.0.1:23119/api/`, no key), live, and
nothing is kept on disk between runs but the local API key below. It never
opens `zotero.sqlite`; merges happen in the desktop client. The local API is
off until the author enables Zotero Settings > Advanced > "Allow other
applications on this computer to communicate with Zotero"; until then the
helper fails and names that setting. `ZOTERO_CONNECTOR_URL` points it at
another loopback port; if something other than Zotero answers there, the
error says so and names both the variable and the setting. The helper needs
Zotero 10 or later, reads and writes alike, and refuses an older client by
name. Lookups ask Zotero's own search for each key; no command but
`report-duplicates` reads the whole library. A read Zotero does not finish in
time is reported as such (`zotero: "slow"`, verdict `zotero_slow` in
`check-staging`, exit 74), never as Zotero unavailable.

Writes go through the same local API with a local API key, kept as
`ZOTERO_LOCAL_API_KEY=` in `~/.config/keys/zotero-local.env` (mode 600;
`ZOTERO_LOCAL_KEY_FILE` overrides the path) and never printed. On the first
write without a key, or on a 401, Zotero shows an Allow / Always Allow / Deny
dialog and the helper waits up to 120 s for the answer, before writing
anything. **Tell the user to answer "Always Allow"**: the helper accepts and
stores only that key. A one-time "Allow" answer is refused and nothing is
written. An attachment counts as a stored file only when Zotero reports its
md5 or size.
`create-items` creates new items and uploads their PDFs; `create-items
--dry-run` also needs Zotero running, because field placement uses the live schema. When Zotero is not running the helper
launches it and waits; in a container, or with `ZOTERO_NO_LAUNCH` set, it
never launches anything. If Zotero
still does not answer, the command does nothing and says so (exit 75;
`check-staging` exits 0 with verdict `zotero_unavailable`). Existing items
are edited only with `--edit`: `suggest-edits`, `suggest-attachments` and
`check-staging --apply` report the edit (item key, field, old → new) by
default and write it only when `--edit` is passed (`check-staging`: `--apply
--edit`; `--edit` alone is an error); `check-staging --apply` alone creates
only the absent items. When Zotero is not running nothing is created, and
the entries JSON is what to rerun later.

## A scraped identifier is a hypothesis, not a finding

`find_identifier` regexes DOIs and arXiv ids out of page text, and page text
contains the reference list. The id it returns is frequently a **cited work's**,
not the document's own — and resolving it through CrossRef returns clean,
well-formed, confident, wrong metadata that nothing downstream questions. In a
158-PDF backfill this produced a Cottle memoir filed as an Albers paper on
Ronald Graham, a Parise–Ozdaglar item filed as Diaconis & Janson 2007, and a
Le Cadre item filed as Foti 2018.

So check every resolved record against the document's own words before
accepting it: read the first page (`first_pages_text` in `extract-metadata`'s
output) and confirm that the resolved title and first author are this
document's. The helper does not score this for you: the judgment is yours. When the resolved title and first
author do not appear on the page, the identifier is a cited work's: discard
the resolution and rebuild the metadata from the text, the filename, and a
web search. Cross-check against the project `.bib` where one exists: it is
curated by the author, so it confirms, though it can be terse or stale and
does not replace reading the page.

The same discipline applies to the year: a `date` on the Zotero item can be a
reprint or translation date (Kantorovich 1942 recorded as 2004), so a year
mismatch alone is not evidence of a wrong match.

## Output to the user

End your turn with:

- One line per item (PDF or URL): title (orig) — `[type]` — `created` (with the new item key) or the reason it was not — duplicate verdict.
- When Zotero was unavailable, the path of the entries JSON to rerun `create-items` with.
- A reminder about Zotero deduplication if any duplicate-risk entry was imported.
