---
name: reading-note
description: "Critical reading note (note de lecture) on one article or book, filed in Zotero."
disable-model-invocation: false
user-invocable: true
argument-hint: "<DOI | citation | PDF path | Zotero item>"
---

# Reading note

A critical reading of one whole work, written so that the note substitutes for
re-reading it. Distinct from `related-work-note`, which defends one paragraph of
the author's manuscript against a referee; a reading note serves the work, not
a paragraph. `critical-lit-review` fans out to this skill for the works it
selects.

Discipline: `rules/edm.md`. Zotero is the system of record; `docs/` is staging.

## 1. Get the work and its metadata

- **Full text first.** Follow the edm.md chain: `docs/` → Zotero → ISTEX →
  open web → author. A paywall is not inaccessibility until ISTEX has answered;
  a scan without a text layer goes through `ocrmypdf`. Never write a note from
  an abstract and say so if the full text could not be had.
- **Intake.** If the work is not in Zotero yet, file it first: `zotero-import`
  for a PDF, `index-source` for a URL. They resolve the identifier, dedupe and
  attach the file; do not duplicate their lookups here.
- **Metadata from the first page**, not from PDF metadata fields:
  `pdftotext -f 1 -l 1`. A DOI scraped from the text may be a cited work's;
  corroborate it as `zotero-import` describes before trusting it.

## 2. Get the research context

The Research relevance section needs the author's question. Read it from the
project before asking: the scoping document of a `critical-lit-review` run,
the brief a delegating skill passed in, the manuscript, `STATE.md`. Ask the
author only for what none of these states, in one round.

## 3. Write the note

Follow `references/template.md`, the single reading-note template. What the
template cannot enforce:

- **Read the whole work.** Skim-and-summarise produces the abstract back.
- **Separate the author's claims from yours**: "X argues" for theirs,
  unhedged analysis for yours, never blended in one sentence.
- **Assumptions in three kinds**: explicit (acknowledged givens), implicit
  (taken for granted), naturalized (presented as technical or self-evident
  when contingent or political). The third is what the note exists for.
- **Position it** in the conversation it joins: whom it answers, cites, ignores.
- **Every quotation carries the page read on the page**, per edm.md: extract
  the single page (`pdftotext -f N -l N`) and read its folio. An interpolated
  locator is worse than none. When a claim turns on formal content, check that
  the extraction kept the equations.
- **HET register**: the author is a historian of economic thought; write for an
  informed reader in that field, not for a general audience.

## 4. Store it

1. Stage the note as `docs/<AuthorYear>_<ShortTitle>.md` (git-ignored staging).
2. Archive it with `index-source` as its own **Document** item (the research-note
   row of its type table), titled `Reading note: <work title>`, with the work's
   DOI or Zotero item key in the note's metadata block so the two link up.
3. When a `critical-lit-review` run delegated the note, also leave the path in
   the run's working directory it named.

## Output to the user

One line: work title — Zotero item of the work — Zotero item of the note —
full text read (yes / abstract only, why) — word count. Then the three findings
that matter most for the author's question, one line each.
