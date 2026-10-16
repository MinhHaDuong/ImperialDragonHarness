---
name: zotero
description: "Import one or more PDFs or URLs into Zotero, suggest enrichments to existing items, or audit and reconcile the library — extract metadata, resolve identifiers online, dedupe against the running Zotero's local API, and create items with their PDFs through its desktop connector (RIS file as fallback)."
disable-model-invocation: false
user-invocable: true
argument-hint: "import <pdf-or-url>... | enrich | audit <dir> | reconcile <repo> | dedup-report | attach"
---

Discipline: `rules/zotero.md` — Zotero is the system of record, `docs/` and `.bib` are git-ignored staging. It is no longer resident in every session (ticket 0572); read it before working outside the verb files. A cited page number is read on the page, never interpolated from an extraction (the rule carries the discipline).

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
| `enrich` | report missing fields on items that already exist, for the author to fill | `references/enrichment.md` |
| `audit` | report a staging directory or BibTeX-linked repository against the library | `references/backfill.md` |
| `reconcile` | repair the staging ↔ library correspondence (report-only by default) | `references/backfill.md` |
| `dedup-report` | hash-dedup report, library against itself (ticket 0485) | `docs/zotero-dedup-report.md` |
| `attach` | report how to file a document onto an item that already exists | `references/backfill.md` |

The former three modes dissolve into this surface: `import` and `enrichment`
map to the `import` and `enrich` verbs, and the backfill mode splits between
`audit` and `reconcile` — a staging sweep is not the import happy path
repeated N times, which is why `references/backfill.md` stays as the shared
reference for those two verbs. The former index-source skill (URL intake) is
absorbed into `import`: a URL is one more input, probed by the skill's own
`probe-url.py` script.

`match` and `write` are shared plumbing, not user verbs: `match` serves
import and audit both, and `write` is the durable-RIS step behind import.
`references/helper-script.md` documents every subcommand and the guarantees
of its output (`why` / `certainty` / `consulted` / `skipped`).

Inside `import`: probe → match → write → inject. `probe` (or
`probe-url.py` for URLs) extracts, `match` dedupes against a live read of
the library, `write` emits the durable RIS artifact, and `inject` creates the
items through the Zotero desktop connector. `references/import.md` carries
the full contract.

## Safety contract

The helper is local-only and stateless. Every library read goes through the
running Zotero's local API (`127.0.0.1:23119/api/`, read-only, no key), live,
and nothing is kept on disk between runs. It never opens `zotero.sqlite`;
merges happen in the desktop client. The local API is off until the author
enables Zotero Settings > Advanced > "Allow other applications on this
computer to communicate with Zotero"; until then the helper fails and names
that setting.

The only write is the creation of new items with their PDFs, through the
desktop connector on the same port. When Zotero is not running the helper
launches it and waits; in a container, or with `ZOTERO_NO_LAUNCH` set, it
never launches anything. If Zotero
still does not answer, the command does nothing and says so (exit 75;
`reconcile` exits 0 with verdict `zotero_unavailable`). Existing items are never
edited by the helper: `enrich`, `attach` and `reconcile` report the edit
(item key, field, old → new) for the author to make in the client;
`reconcile --apply` creates only the absent items. The
RIS file is the durable artifact and remains the fallback when Zotero is not
running.

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

## Output to the user

End your turn with:

- One line per item (PDF or URL): title (orig) — `[type]` — `created` (the connector returns no item key) or fallback/xdg-open status — duplicate verdict.
- The RIS file path (artifact, and the fallback import route).
- A reminder about Zotero deduplication if any duplicate-risk entry was imported.
