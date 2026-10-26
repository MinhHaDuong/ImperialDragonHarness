---
metadata:
  category: research
name: biblio-saturation
description: "Saturate a factual register or novelty claim with independent searches across fields, languages, gray literature and citation trails; adversarially judge candidates and completeness."
disable-model-invocation: false
user-invocable: true
argument-hint: 'register file path + novelty claim location, e.g. "conception/registre-verification-p1.md, claim = ligne 1"'
---

# Bibliographic saturation pass

An auditable search of an explicit factual register or novelty claim.
Every conclusion rests on consulted evidence; every serious prior-art candidate
faces adversarial judgment. Saturation is bounded by the claim, search scope
and cutoff, never proof that no prior work exists anywhere.

## Inputs and scope

Accept either or both, and run only the supplied workload:

- **Factual register**: numbered claims, criticality, and existing statuses
  `à contrôler` / `confirmé` / `nuancé` / `réfuté`. This calls for source
  verification, not a full novelty sweep for each citation.
- **Novelty claim**: exact statement and location, what would refute it
  (equivalent propositions in other vocabularies included), fields, languages,
  period, document types, cutoff, and the available search effort / stop bound.
- Context paths readers may consult, existing candidate/consultation table,
  reading notes and search history when present. Searchers never edit these.

Without a refutable novelty claim, return corpus leads or factual checks with
that limited scope; do not invent a claim or declare a whole corpus saturated.
For a few nearby references, use a targeted search and
[related-work-note](../related-work-note/SKILL.md). A full claim sweep requires
its own scope. Corpus discovery belongs to
[critical-lit-review](../critical-lit-review/SKILL.md); a later lacuna claim
can reuse its search history and notes as inputs here.

## Runtime and concurrency

Discover available search, full-text retrieval and delegation capabilities
before launching. Use the `route` skill for worker choice and reviewer
independence (`skills/route/references/decorrelation.md`). This skill explicitly
authorizes delegation when available. Independent searches run
**parallel-background**, within the runtime's available capacity, with separate
briefs blind to the other searchers' yields. Rounds and search → cross-check →
judgment → completeness assessment are **sequential-blocking**, since each
consumes the preceding evidence.

With one slot, run angle briefs sequentially, preserving separate query logs
before pooling their results. Keep the adversarial verification pass distinct
and reconsult sources; report that a same-worker pass lacks an independent
reviewer. If a required capability is missing, use accessible scholarly search
interfaces or APIs (e.g. OpenAlex, Crossref, arXiv, disciplinary repositories)
and record the fallback's actual coverage. If none can search an angle, mark
`angle_blocked`; a failed tool call is not an executed search.

### Phase 1 — factual register

For each open line, resolve the attribution against primary sources. A
cross-checker reconsults sources itself and checks venues, years, pages,
theorem numbers and attribution order. Verdicts: `confirmé` (as stated),
`nuancé` (with corrections), `réfuté`, or `unresolved` (insufficient evidence,
including inaccessible text). Include page/section evidence and safe wording;
for an unresolved claim, wording must retain the uncertainty or omit it.

### Phase 2 — novelty search

Assign distinct angles adapted to the claim; record why each relevant family
is searched or excluded. Preserve diversity across:

- **Fields and lateral vocabularies**: equivalent objects and propositions in
  adjacent disciplines, including older terminology and pre-war literature.
- **Structured queries**: intersect terms and synonyms in disciplinary and
  general scholarly indexes.
- **Languages**: relevant non-English traditions and national repositories
  (e.g. French, Russian, Chinese, Japanese, German); justify the selection.
- **Gray literature**: theses, working papers, institutional repositories.
- **Citation graph**: backward/forward trails from pivot works.
- **Recency**: recent preprints and material not yet indexed elsewhere.
- **Textbooks and surveys**: possible folklore statements and older sources.

Optional HAL access: [HAL discovery](../../docs/hal-discovery-mcp.md) when
available; direct HAL API remains a fallback. The pointer loads no tools.

For each angle retain queries, interface/date, returned leads, sources actually
fetched, abstracts versus full texts read, and exclusions. Follow promising
citation trails and revise queries when terminology changes. Query counts are
not coverage evidence. Report located candidates as potential `preempts`,
`adjacent`, or `background`, with provenance; empty results need no padding.

After pooling and deduplication by identifiers and normalized title/year,
launch fresh or revised angles against the uncovered scope. A dry round adds
no new serious preemption/adjacency candidates **after its planned searches
actually ran**. A failed, skipped or blocked angle cannot count as dry.
Stop at a dry round only after the relevant angle families and citation leads
have been examined and the completeness assessment below agrees. At the
agreed effort/stop bound, return partial results and remaining work instead
of forcing a saturation verdict.

### Phase 3 — adversarial judgment

For each serious candidate, a judge reconsults the primary text and records
one of:

- `preempts`: passage states, proves or implies the scoped claim.
- `must_cite`: nearby work that must be cited and distinguished.
- `does_not_preempt`: positive textual evidence shows the relevant difference;
  state that difference and its locator, not just low confidence.
- `unresolved`: identity, interpretation or access remains uncertain. Name
  the missing evidence and the retrieval attempts; inaccessible text is never
  evidence of non-preemption. A finder description or abstract alone cannot
  settle a claim requiring the proof or full argument.

Use the `rules/zotero.md` access chain for missing full text and verify folios
on the page. Record what was actually read. Confidence never substitutes for
a passage supporting a verdict.

### Phase 4 — completeness assessment

A critic checks the logs, exclusions, unresolved candidates and angle coverage,
and probes searches itself. Record its independence or lack thereof. Missing
angles lead to another bounded search/judgment round when capacity remains;
otherwise return them as pending. An unavailable engine may be covered by an
adequate fallback, but that equivalence needs a stated reason.

Declare `saturated_within_scope` only for the explicitly examined scope when
no material angle remains blocked, no potentially decisive candidate remains
unresolved, and the dry-round and critic requirements hold. Otherwise declare
`partial` with `angle_blocked` and `unresolved` entries. Any narrowing of scope
must be explicit in both the report and the novelty wording; the original
broader claim remains unverified. Even a saturated search may establish
preemption: coverage and the scientific verdict are separate.

## Outputs

- Register updates with verdicts, safe wording, primary-source locators and
  remaining unknowns. The coordinator alone edits the register.
- Claim report: exact claim/scope/cutoff, executed search logs and round yields,
  deduplicated candidates and judgments with passages, texts actually read,
  `must_cite` list, `unresolved` candidates, `angle_blocked` entries and reasons,
  critic's assessment and coverage status. Feed the citation distinctions to
  `related-work-note`; feed evidence-supported gap wording back to the review.
- A ticket log when working on a ticket; commit authorized project changes on
  a branch. Do not create a new bibliography or corpus catalog here.

## Failure modes this protocol exists to catch

- **Plausible-but-wrong finder claims** — hence judges that re-fetch, and
  an explicit unresolved outcome for thin evidence.
- **Search-angle monoculture** — five prior AI passes each missed a family;
  variety across fields, languages and eras is the countermeasure.
- **Premature stop** — hence dryness looping plus an explicit critic, not a
  fixed round count.
- **Unusable positives** — a verdict without a safe wording or a resolvable
  source is not a verdict.
