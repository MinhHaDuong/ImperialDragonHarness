---
name: critical-lit-review
description: "Critical literature review (état de l'art) in history of economics and STS: object, actors, controversies."
disable-model-invocation: false
user-invocable: true
argument-hint: "<research question, abstract, notes or draft>"
---

# Critical literature review

Map a field as a historian of economic thought would: construct the object,
name the actors, expose what the literature does not debate, and position it in
intellectual history. The output is an analytical report, not a descriptive
survey. Scope is a whole field; for defending one paragraph of a manuscript,
use `related-work-note` instead.

**A review constructs a scientific object, not a theme.** "Climate finance" is
a theme; "climate finance as an economic object constructed through OECD
quantification practices, 1990–2025" is an object. Every later step is
organized by the object and its axes, never by chronology alone, which hides
the tensions the review exists to show.

The author's materials can be anything: a question, an abstract, notes, a
draft, a bibliography. Ask at most three questions per message.

## 1. Construct the object

Produce `scoping.md` in the run's working directory, and get the author's
agreement on it before searching. It states:

- **The object**, in two or three sentences, as constructed above.
- **One guiding question**, of the form "How was X constituted as Y by Z?",
  "What theoretical tensions structure debates over X?", or "How do actors X
  naturalize category Y through practice Z?".
- **Delimitation, each bound justified**: period (why these start and end
  dates), main field and admitted adjacent fields, central institutional
  actors, languages, document types (gray literature included or not).
- **Exclusions, each justified**: out of period, out of field, out of
  tradition.
- **Three to five analytical axes.** Each must classify the corpus, compare
  authors and reveal tensions or ruptures: economic categories mobilized,
  quantification tools, institutional roles of economists, methodological
  controversies, performative effects of numbers are typical.

## 2. Build the corpus

- **Search with `biblio-saturation`**: its angle taxonomy (fields, languages,
  gray literature, citation trails, recency) and its dryness criterion are the
  search protocol. Seed it with the scoping document's object, axes and
  languages, the author's own publications and frequent co-authors. Do not run
  a separate ad hoc crawl.
- **Optional HAL transport**: [HAL Discovery MCP](../../docs/hal-discovery-mcp.md),
  activated only for this task; direct HAL API remains a fallback. This
  pointer does not register or load MCP tools.
- **Pool every candidate raw, then screen once with one rule** derived from
  the scoping document. Never screen sources iteratively as they arrive, and
  never add records screened by one rule to a corpus filtered by another.
- **Consultation table** (`consultation.csv`): one row per candidate, columns
  `id, found_by, type, authors, year, title, doi, url, keep, read_note,
  justification`. The justification is short and names the scoping criterion
  it applies.
- **Full text** for kept sources follows the `rules/zotero.md` chain (`docs/` →
  Zotero → ISTEX → open web → author). A source is not inaccessible until that
  chain has run; record which step failed in `justification`.
- **Intake** of kept sources into Zotero goes through `/zotero import` (PDF or
  URL alike). Zotero, not the run directory, holds them.

Corpus is complete when the seminal works, the last two or three years, the
key methodological documents, every major institutional position and every
main theoretical tradition are represented, and the saturation critic agrees.

## 3. Reading notes

Select the works that warrant a full critical reading (`read_note` in the
table): seminal works, direct precedents, methodological exemplars, one
representative per position in each controversy, the author's own key
publications. Usually fifteen to twenty-five.

Delegate each to `reading-note`; do not write notes inline. Launch the
readers **parallel-background, in batches of at most 8**: the notes are
independent of one another, and the batch bounds coordination overhead.
Choose the worker per the `route` skill on every launch: a note is bulk
interpretive work, and the synthesis below stays with the coordinating
session. Each brief carries the
citation, the staged full text or Zotero item, the scoping document, and why
this work was selected (axis, controversy, position). Steps 4 to 6 start only
when the whole batch has returned: they read across notes.

## 4. Map the actors

From the table and the notes:

- **Scholars and institutions** that recur (three or more works in the corpus),
  with affiliations and their changes over time: careers between academia,
  international organizations, governments and advocacy are themselves data.
- **Roles**: *category producers* (who coined the concepts, in which
  institutional setting, with what authority), *normalizers* (who turned
  practice into guidelines and official methodology), *critics* (from which
  theoretical or institutional position, proposing which alternatives).
- **Coalitions**: who cites whom approvingly or critically, co-authorship,
  institutional partnerships, shared framings (efficiency against justice,
  technical against political).
- **Profiles** for the ten to fifteen key actors: trajectory, disciplinary
  home and frameworks, normative commitments, position in each debate and how
  it moved.

## 5. Controversies, explicit and silent

- **Explicit controversies**: methodological, empirical (which numbers are
  contested, which counts compete) and theoretical. For each: protagonists,
  positions, evidence marshalled.
- **Silent controversies are the core deliverable.** What no side debates:
  choices framed as technical, categories used without definition, historical
  contingency presented as nature, perspectives and actors never cited,
  questions never asked, a consensus every side shares that should not be
  taken for granted.
- **Stakes behind each**: whose interests a framing serves, which mandates
  shape the arguments, who holds the authority to define categories, how a
  definitional choice moves resources, what would change under the
  alternative.

## 6. Position in intellectual history

- **Traditions**: history of quantification (Desrosières, Porter, Espeland),
  performativity and STS (Callon, MacKenzie, Latour), and the disciplinary
  lineages of the economics involved: which predecessors the current
  frameworks continue or break with, which path dependencies show.
- **The lacuna**: an institutional blind spot, a missing historical depth, a
  missing comparison, a confusion of category with instrument, or an
  unapplied method. Keep it only if it is real (absent, not merely
  dispersed), documentable with available sources, tractable in the project's
  scope, and significant to a journal's readers. A lacuna claim is a novelty
  claim: put it through `biblio-saturation` before the report states it.

## 7. Report

Write `report.md` (or LaTeX, per the project) following
`rules/doctype/techreport.md`. Length follows from the material and the
destination; when a budget applies, cut with `cut-prose`. Sections, adapted to
the object:

1. Introduction: object, guiding question, stakes, lacuna, scope.
2. Institutional genealogy: actors, emergence of the categories, authority to
   define.
3. Measurement practices and methodologies.
4. Explicit controversies, by protagonist and position.
5. Silent controversies and naturalized assumptions.
6. Historiographical positioning and contribution.
7. Conclusion and research agenda.

Analytical throughout: "X's argument naturalizes Z by framing it as W", not
"X argues Y". Every specific claim cited, with a page locator read on the page
(`rules/zotero.md`). Name actors, cite documents.

## 8. Bibliography

Annotated bibliography of the works the report cites, and only those:
organized by theme to show the field's structure, two to four sentences per
entry on contribution and position, a resolving DOI or URL for every entry.
Every cited work is already in Zotero from the intake in step 2; a project
`.bib` is staging exported from it (`rules/zotero.md`).

## Output to the user

The run directory's files (`scoping.md`, `consultation.csv`, reading-note
items, `report.md`, bibliography), one line each; the corpus funnel (pooled,
kept, read); the saturation critic's verdict; the lacuna as stated; and any
source that stayed inaccessible after the full zotero.md chain, with where it
failed.
