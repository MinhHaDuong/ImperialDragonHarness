---
name: biblio-saturation
description: Saturation bibliographic search by independent web-search subagents — adjudicate factual register lines and adversarially stress a novelty claim until every search angle runs dry. Fleets of finders on disjoint angles (fields, languages, gray literature, citation graph, lateral vocabularies), adversarial judging of every candidate, completeness critic before declaring saturation.
disable-model-invocation: false
user-invocable: true
argument-hint: register file path + novelty claim location, e.g. "conception/registre-verification-p1.md, claim = ligne 1"
---

# Bibliographic saturation pass

Replace a human librarian pass with a multi-agent sweep that is *auditable*:
every verdict cites a source that an agent actually resolved online, every
candidate preemption survives an adversarial judge, and the sweep only stops
when new angles stop producing new candidates.

Two workloads, run in one Workflow invocation:

1. **Factual register lines** — attributions, exact statements, publication
   venues. Cheap to verify, expensive to get wrong in print.
2. **A novelty claim** — usually negative ("no prior work states X"), the kind
   of claim that carries a paper and that search bias systematically
   under-tests. This is the part that needs saturation, not spot checks.

## Inputs

- A verification register: numbered lines, each a claim with a criticality
  level, statuses `à contrôler` / `confirmé` / `nuancé` / `réfuté`.
- The novelty claim, stated precisely enough to refute: the mathematical
  setting, the exact proposition, and what would count as prior art
  (equivalent statements in other vocabularies included).
- Paths to context files (draft, notes) agents may read. Agents never write.

## Protocol

Orchestrate with the Workflow tool (this is an explicit multi-agent skill;
invoking it is the opt-in). All fan-outs run **parallel-background in batches
of at most 8** — the authorized concurrency ceiling; batching trades a little
wall-clock for bounded coordination overhead. Rounds are
**sequential-blocking**: the dryness test needs the full round's yield.

Pin models per launch (frontmatter does not propagate): finders `sonnet`,
judges and critic `opus` — verifier model must differ from producer model.

### Phase 1 — register lines (parallel pipeline, one chain per line)

For each open line: one web searcher resolves the claim against primary
sources (DOI, arXiv, publisher, DBLP); then an independent cross-checker
**re-fetches the sources itself**, corrects venues, years, pages, theorem
numbers and attribution order, and emits the final verdict. Verdict grid:
`confirmé` (exact as stated), `nuancé` (right but needs stated corrections),
`réfuté`. Every verdict includes a *safe wording* — the English sentence the
manuscript may actually use.

### Phase 2 — novelty-claim sweep (rounds, loop until dry)

Rounds of up to 8 finders, each assigned one angle, blind to the others.
Draw angles from this taxonomy and adapt to the claim:

- **Disciplinary fields**: each field that could have found the result under
  its own name (for pricing claims: mathematical finance, market
  microstructure, DeFi/MEV, constraint satisfaction, OR flows, spatial
  economics, econophysics).
- **Structured queries**: the intersection queries a librarian would run
  (term × term across Scopus-like engines).
- **Languages**: French, Russian, Chinese, Japanese, German — via zbMATH,
  Math-Net.ru, theses.fr, HAL, national repositories.
- **Gray literature**: PhD theses, SSRN and central-bank working papers,
  institutional repositories.
- **Citation graph**: forward/backward citations of the pivot papers
  (Semantic Scholar / OpenAlex APIs), filtered by the claim's vocabulary.
- **Recency**: last-24-months arXiv categories, not yet indexed elsewhere.
- **Textbooks and surveys**: where a folklore version of the claim would be
  recorded as a remark.
- **Lateral vocabularies**: the same mathematical object under other names
  in other fields; classics and pre-war literature (archive.org).

Finder contract: at least 6–10 distinct queries per angle, follow citation
trails, report only candidates actually located (abstract or full text
fetched), classified `preempts` / `adjacent` / `background`. An empty
candidate list is a good answer — no padding with background papers.

**Dryness criterion**: stop after a round that adds zero fresh
`preempts`/`adjacent` candidates (dedup by normalized title+year), minimum
two rounds. Simple round counts miss the tail; dryness is the point.

### Phase 3 — adversarial judging (parallel batches of 8)

Every fresh serious candidate goes to a judge that **fetches the source
itself** and rules: `preempts` (genuinely states/proves/implies the claim),
or `must_cite` (nearby; cite and distinguish), with confidence. Default to
*not preempting* when evidence is thin or the source cannot be verified —
the finder's description is a lead, not a fact.

### Phase 4 — completeness critic, then one final round

One critic reviews the angles run and the yield, probes a few searches
itself, and either declares saturation or returns up to 8 missing angles.
Missing angles trigger exactly one more find+judge round. Never declare
saturation silently: the critic's assessment is part of the report.

## Web tooling resilience

Agents load `WebSearch`/`WebFetch` via ToolSearch. If WebSearch is
unavailable, fall back to WebFetch on: Semantic Scholar
(`api.semanticscholar.org`), OpenAlex (`api.openalex.org`), Crossref
(`api.crossref.org`), arXiv export API, DBLP, `doi.org`. State the fallback
used in the report.

## Outputs

- Register file updated: each adjudicated line gets verdict, findings with
  page/section pointers, verified sources, safe wording.
- Novelty-claim report: rounds run and yield per round, judged candidates
  with verdicts, the must-cite list (feeds the related-work section — see
  [related-work-note](../related-work-note/SKILL.md)), the critic's
  saturation assessment.
- Ticket log entry recording protocol, rounds, and verdict; commits on a
  branch per git discipline.

## Failure modes this protocol exists to catch

- **Plausible-but-wrong finder claims** — hence judges that re-fetch, and
  the thin-evidence-means-no default.
- **Search-angle monoculture** — five prior AI passes each missed a family;
  variety across fields, languages and eras is the countermeasure.
- **Premature stop** — hence dryness looping plus an explicit critic, not a
  fixed round count.
- **Unusable positives** — a verdict without a safe wording or a resolvable
  source is not a verdict.
