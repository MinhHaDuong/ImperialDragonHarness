---
name: zotero-import
description: "Import one or more PDFs into Zotero, or backfill a whole staging directory — extract metadata, resolve identifiers online, dedupe against the library (desktop database or a cached Web API index), and inject items with their PDFs through the Zotero Web API (RIS file as fallback)."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pdf>... | audit <dir>"
---


Discipline: `rules/edm.md` — Zotero is the system of record, `docs/` and `.bib` are git-ignored staging. It is no longer resident in every session (ticket 0572); read it before working outside the mode files.
# Zotero import

Build the metadata for one or more PDFs, then `inject` items and attachments directly through the Zotero Web API (decided 2026-08-13; previously the flow ended at `xdg-open` on a RIS file and a human confirmation click). The RIS path remains the fallback when no read-write key is available or the user asks for a manual import.

## Modes

Three modes, and a run is in exactly one. They are not variants of each other —
a staging directory is not the single-file path repeated N times, and enrichment
writes to items that already exist. **Read the mode's file before acting.**

| mode | when | file |
|---|---|---|
| import | one or more PDFs to file as new items | `references/import.md` |
| enrichment | the item exists; fields are missing | `references/enrichment.md` |
| backfill | reconcile a whole staging directory | `references/backfill.md` |

`references/helper-script.md` documents the `zotero-import.py` lookup and write
subcommands and the guarantees of their output (`why` / `certainty` / `consulted` / `skipped`).
Read it alongside the mode file: `match` serves import and backfill both, which
is why it is one shared reference rather than copied into each mode.

The two sections below govern every mode.

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

- One line per PDF: title (orig) — `[type]` — item key (or fallback/xdg-open status) — duplicate verdict.
- The RIS file path (artifact, and the fallback import route).
- A reminder about Zotero deduplication if any duplicate-risk entry was imported.
