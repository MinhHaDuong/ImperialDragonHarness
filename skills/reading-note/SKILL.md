---
metadata:
  category: research
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

Discipline: `rules/zotero.md`. Zotero is the record for works and reading notes; `docs/` is staging; the repository holds drafts under review.

## 1. Get the work and its metadata

- **Full text first.** Follow the zotero.md chain: `docs/` → Zotero → ISTEX →
  open web → author. A paywall is not inaccessibility until ISTEX has answered;
  a scan without a text layer goes through `ocrmypdf`. Never write a note from
  an abstract and say so if the full text could not be had.
- **Intake.** If the work is not in Zotero yet, file it first with the zotero skill
  import — PDF or URL. It resolves the identifier, dedupes and
  attaches the file; do not duplicate its lookups here.
- **Metadata from the first page**, not from PDF metadata fields:
  `pdftotext -f 1 -l 1`. A DOI scraped from the text may be a cited work's;
  check it against the page as the `zotero` skill describes before trusting it.

## 2. Get the research context

The Research relevance section needs the author's question. Read it from the
project before asking: the scoping document of a `critical-lit-review` run,
the brief a delegating skill passed in, the manuscript, `STATE.md`. Ask the
author only for what none of these states, one question at a time, after
asking up (`rules/workflow.md` § Escalation protocol, § Autonomous action).

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
- **Every quotation carries the page read on the page**, per zotero.md: extract
  the single page (`pdftotext -f N -l N`) and read its folio. An interpolated
  locator is worse than none. When a claim turns on formal content, check that
  the extraction kept the equations.
- **HET register**: the author is a historian of economic thought; write for an
  informed reader in that field, not for a general audience.
- **Anchor what you claim.** Every main finding and every naturalized
  assumption cites a numbered quotation [Qn] from Key quotations. A note
  drafted by a model reaches `status: quotes verified` only after each quotation
  is matched verbatim on its stated page of the text; until then it stays
  `draft`. The author's revision makes it `author revised`, the authoritative
  version.
- **Open access and reproducibility** are recorded, not guessed: `open_access`
  from the copy actually used or from Unpaywall/OpenAlex; for an empirical work,
  look for a replication package (journal supplement, repository, author page),
  record whether it was accessed, and what verification was attempted and at
  what effort, even if the answer is "not attempted".
- **Length by tier**: full for the deep-read tier, short for the skim tier
  (see the template). The project sets the word caps; the harness fixes none.

## 4. Store it

The filed note is an **HTML child note** under the work's Zotero item, reached
through the local API only (never the Web API). Run these steps
**sequential-blocking**: each consumes the preceding output.

1. Write the draft in the project's drafts directory (default
   `reading-notes/<AuthorYear>_<ShortTitle>.html`; a project may name another,
   such as `wiki/works/`), on a branch, in the format of
   `references/template.md`. Never in `docs/`.
2. `zotero_item` is the **exact key** of the work's item, read from Zotero
   (`zotero` skill, find-work), never guessed from a filename or title. No item
   yet: import the work first (§ 1).
3. Review and merge the draft by the project's route. After merge, publish with
   `zotero publish-notes`, which files the HTML as a child note of
   `zotero_item` and reads it back. If publishing is blocked, report it pending
   and keep the draft on the branch.
4. Zotero's note is then authoritative; the repository keeps the draft and any
   generated snapshot, which are never edited to diverge from it.
5. **Superseding an old filing.** A standalone Document with an `.md`
   attachment from the earlier workflow is left in place, not migrated
   automatically. When the work is re-noted, publish the new child note, then
   tell the author which old Document it supersedes so they can retire it; do
   not delete it.
6. When a `critical-lit-review` run delegated the note, also leave the draft
   path in the run's working directory it named.
7. When the note belongs to a project corpus (`work_key` set) and the project
   keeps a coding dataset, append the frontmatter there as one record keyed by
   `work_key`, so syntheses query the dataset rather than parse notes.

## Output to the user

One line: work title — Zotero item of the work — draft path —
publication receipt (child note key) or pending reason — full text read (yes / abstract only, why) — word count. Then the three findings
that matter most for the author's question, one line each.
