---
metadata:
  category: research
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

- **Corpus discovery** starts from `scoping.md`: turn its axes, fields,
  languages, period and document types into a search plan, with the author's
  publications and frequent co-authors as seeds. Use the diverse angle
  taxonomy of `biblio-saturation` (including gray literature and citation
  trails), without asking it to saturate a corpus as if it were a novelty
  claim. Retain queries, interfaces/dates, yields and blocked angles; agree
  a practical stop bound and assess coverage against the scoped object.
- **Optional HAL transport**: [HAL Discovery MCP](../../conception/hal-discovery-mcp.md),
  activated only for this task; direct HAL API remains a fallback. This
  pointer does not register or load MCP tools.
- **Pool every candidate raw, then screen once with one rule** derived from
  the scoping document. Never screen sources iteratively as they arrive, and
  never add records screened by one rule to a corpus filtered by another.
- **Consultation table** (`consultation.csv`): one row per candidate, columns
  `id, found_by, type, authors, year, title, doi, url, keep, read_note,
  justification, access_status, access_attempts, zotero_item, note_item`.
  `found_by` links to the search log; `access_status` distinguishes full text,
  abstract only, inaccessible and not attempted; item columns hold library/key
  and stay empty until stored. The justification is short and names the scoping criterion
  it applies.
- **Full text** for kept sources follows the `rules/zotero.md` chain (`docs/` →
  Zotero → ISTEX → open web → author). A source is not inaccessible until that
  chain has run; record which step failed in `justification`.
- **Intake** of kept sources into Zotero goes through the zotero skill's `import` (PDF or
  URL alike). Zotero, not the run directory, holds them.

Assess corpus coverage against the agreed period, traditions, institutional
positions, methods and current work within the cutoff. Record excluded and
uncovered areas. A major inaccessible source or blocked search leaves that
coverage partial; do not infer a literature gap from it. Corpus coverage is
separate from the later saturation of a particular novelty claim.

## 3. Reading notes

Select the works that warrant a full critical reading (`read_note` in the
table): seminal works, direct precedents, methodological exemplars, one
representative per position in each controversy, the author's own key
publications. Selection follows their analytical role, not a target count.

Use `reading-note` for each selected work, passing its citation, full text or
Zotero item, corpus id, scoping document, and selection reason (axis,
controversy, position). Discover retrieval and delegation capabilities first.
When delegation is available, readers run **parallel-background** within the
runtime's capacity; choose workers through `route`. With one slot, invoke the
same reading-note contract sequentially in the coordinating session. These
notes are independent; steps 4 to 6 are **sequential-blocking**, starting when
the selected notes have returned or their missing evidence is explicitly
recorded. Update `consultation.csv` with read status and archived note item /
receipt; inaccessible full text remains a coverage limit, never a fabricated
reading note.

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
- **Profiles** for the actors central to the scoped question: trajectory, disciplinary
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
  claim: before stating it, pass `biblio-saturation` its exact proposed
  wording and location, what would refute it, scoped fields/languages/period,
  cutoff and effort bound, with `scoping.md`, `consultation.csv`, search logs
  and relevant reading-note keys/receipts. Bring its candidate judgments and
  coverage status back into the table and report. Unresolved precedents or
  blocked angles require qualified wording or withholding the lacuna claim;
  a review with no novelty claim needs no saturation verdict.

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
kept, read); corpus coverage and blocked angles; the claim-specific saturation
assessment when run (otherwise not applicable); the lacuna as stated or
withheld; and any source that stayed inaccessible after the full zotero.md chain, with where it
failed.
