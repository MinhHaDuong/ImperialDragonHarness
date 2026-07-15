# Vision: Voice-alignment tooling

Status: draft v2 — Imagine stage, revised after a 5-agent panel review
(NLP/stylometry, architecture, product/workflow, privacy, adversarial
skeptic). Not yet approved for build.

## Problem

Prose the author co-writes with an LLM can drift toward "generated"
register — LLMisms, flattened voice, boilerplate phrasing — even after the
mechanical `prose/_all.md` guard list catches the worst tells. Whether there
is a *subtler* drift beyond what that guard list already catches is an
open, unproven hypothesis, not yet demonstrated by a concrete missed case.
Before building further, this vision requires finding (or failing to find)
one.

## Goal

Detect prose that reads as generated or off-voice, grounded in the author's
own writing rather than a generic banned-word list — but only past the
validation gate below. Quality uplift toward stronger models of the genre
(e.g. leading economics journals) is a related but distinct goal, tracked
separately (see Quality-uplift, deferred).

## Non-goals

- Not a generic AI-detector (GPTZero-style) — the corpus is the author's own
  writing, not a population classifier. It inherits that family's known
  fragility anyway (see Known risks), just applied to a personal baseline.
- Not a rewriting-in-the-loop tool — flagging and explaining first; drafting
  assistance is an explicitly later, separately-gated capability.
- Not a replacement for `review-pr-prose`'s existing peer-review panel —
  a candidate extension to it, gated on validation.
- Not a system designed for a mature multi-project fleet. It is designed for
  one author bootstrapping from a small corpus; complexity that assumes
  scale (see Corpus storage) is cut until the corpus actually needs it.

## Known risks in this method family (read before designing further)

- **AI-detector fragility carries over.** Perplexity/burstiness detectors
  (DetectGPT, GLTR-family techniques) are documented to misfire on short
  texts and to have length- and genre-sensitivity problems. A
  personal-corpus variant does not escape this — "distance from your own
  centroid" still degrades on short, jargon-dense, or topically novel
  paragraphs.
- **Genre/topic confound.** Perplexity tracks predictability of content
  (technical density, formulaic sections) as much as authorial style. A
  well-written but jargon-dense paragraph can score as "generated"; boiler-
  plate prose on an unfamiliar topic can score as "surprising." Any per-role
  baseline (the schema's `role` field) needs this confound designed out
  explicitly, not assumed away.
- **Homogenization / regression-to-the-mean.** Scoring against a fixed
  corpus centroid definitionally rewards resemblance to past writing.
  Legitimate stylistic growth or register shift (new topic, new venue,
  the author simply getting better) is statistically indistinguishable, to
  a one-class distance-to-centroid method, from AI-flattening. Countered,
  not eliminated, by the contrastive design below — a paragraph that has
  moved away from both the positive and negative centroids together is
  probably genuine drift; one that has moved specifically toward the
  negative centroid probably isn't. Still never trusted to auto-correct,
  only to flag, with a human dismiss as the final word.
- **Statistical power at paragraph granularity.** Delta-family stylometric
  methods are typically validated on multi-thousand-word samples per class;
  a single paragraph is a noisy unit for both corpus-centroid distance and
  perplexity scoring. Expect a real false-positive rate at this granularity,
  not just a theoretical one.

## Validation gate — before any further build

Convergent finding across every review angle: this vision stacks several
unvalidated layers on an unconfirmed premise. Before committing to
architecture beyond this point (the same local-evidence-gate discipline as
`feedback_local_evidence_gate_for_pillaged_techniques.md` — ticket 0290's
zero-instance wontfix precedent, applied here to a vision doc instead of a
detector implementation):

1. Take the cheapest possible signal — a contrastive stylometric score
   (distance-to-negative-centroid minus distance-to-positive-centroid,
   computed by hand or with a minimal dependency-free function-word-
   frequency + Delta baseline; no library dependency, no finetuning, no
   ensembling) — and run it against a held-out set of **mined real pairs**
   (see Counter-examples): the same paragraph's AI-drafted version and its
   accepted rewrite, for content the author has independent opinions about.
2. Report actual classification accuracy on that held-out set, not a vibe
   check — mined pairs give a real number because both sides of each pair
   share content, controlling for the genre/topic confound above. If
   accuracy isn't good enough to trust, stop — the rest of this document is
   moot regardless of how well-designed the infrastructure is.
3. Only past this gate does corpus-tier investment, perplexity scoring, or
   any further layer get built.

## Scope for v1 (if the gate passes)

Two layers only, both extending `review-pr-prose`'s existing gated-auditor
pattern (matching the AI-tells auditor's role: specialized lint pass, no
other duty):

1. **Stylometric pre-filter** — contrastive score against the user-tier
   corpus's positive and negative centroids (see Corpus storage and
   Counter-examples). Flags paragraphs pulled toward the negative
   centroid, not merely paragraphs far from the positive one — the
   one-class distance version is superseded by this design, not a fallback.
   A dependency-free function-word/Delta baseline is the default, not a
   library, until a library's maturity and French-language coverage are
   separately checked.
2. **LLM qualitative auditor** — a new voice-deviation auditor agent, fed
   the corpus and only the paragraphs layer 1 flagged, explaining the
   deviation in prose.

Everything else below (perplexity scoring, drift tracking, paraphrase
probe, finetuning, multi-model ensembling, quality-uplift) is a **candidate
extension**, described for completeness and future reference, not committed
work. None of it is built before v1 is validated in real use.

### False-positive handling (v1 requirement, not optional)

A dismiss must persist: when the author marks a flagged paragraph as
genuinely in-voice, that paragraph is fed back into the user-tier corpus
(or an explicit "confirmed voice" allowlist) so the same or similar prose
stops re-triggering. Without this, the tool trains the author to ignore it
after a handful of wrong flags — a well-known failure mode for lint-style
tools, and the sharpest edge of the homogenization risk above. A dismiss
feeds back into the corpus as a signal, but v1 has no mechanism that tells a
genuinely-in-voice dismiss apart from one driven by reviewer fatigue — both
write back identically as "confirmed voice" (see Open questions carried
forward).

## Corpus storage (v1: user tier only)

Given the single-author, cold-start reality, v1 builds **one tier**, not
four:

| Tier | Location | Contents | Status |
|---|---|---|---|
| User | `~/data/voice-corpus/user/*.jsonl` | author's own past published/accepted paragraphs | v1 |
| Project | `<project>/config/voice-corpus/*.jsonl` | prose established in earlier chapters/papers of that project | deferred until user tier proves useful and a project corpus is large enough to matter |
| Harness | `~/.claude/config/voice-corpus/harness/*.jsonl` | generic cold-start exemplar set | deferred — only relevant before the user tier has enough material, which v1's gate presupposes it does |
| Manuscript | *(none)* | paragraphs already committed in the current draft | deferred — needs a minimum-word-count gate before it's statistically meaningful (see Known risks); falls back to user tier below that threshold if ever built |

Placement note: the user tier lives under the existing `~/data` directory
(already used for project corpora, e.g. `chemin-de-voix/corpus`) — never a
new top-level directory under `~`, which is not to be restructured for this
or any feature.

Schema (single stored tier for v1; extra fields anticipate — but do not
commit to — later tiers and drift tracking):

```json
{"id": "content-hash of the paragraph text (v1: changes whenever the text changes; edit-stable identity is the unsolved problem named under Drift tracking, not provided here)",
 "text": "...", "source": "...", "role": "intro|method|results|discussion|other",
 "citation": "doi or bare reference", "added_date": "YYYY-MM-DD",
 "coauthored": false,
 "polarity": "positive|negative",
 "pair_id": "id of the counterpart paragraph, if this entry was mined or synthesized as a pair; null for unpaired positives"}
```

`coauthored` defaults to excluding any paragraph with more than one credited
author from ingestion — the corpus profiles the consenting author only; a
co-authored chapter is not fingerprinted without each contributor's
agreement.

`added_date` is stored from the start even though v1 does not act on it, so
that a later staleness policy (down-weighting or reviewing old entries as
the author's voice evolves) does not require backfilling history that was
never captured.

PDFs and HTML sources stay in Zotero + project `docs/` staging per
[edm.md](../rules/edm.md), unchanged. Extraction (`pdftotext` → paragraph
segmentation → filter headers/captions/tables → role-tag → co-author check)
is a one-time-per-source script; the corpus is derived data, not the source
of record, and follows the same retention discipline as other EDM staging —
purge or re-derive rather than treat as permanent.

### Counter-examples — two sourcing methods, not interchangeable

The corpus needs a `negative` class, not just positive exemplars, to make
the contrastive score in the Validation gate and v1 scope possible. Two
distinct sources, weighted differently because they carry different
evidentiary weight:

- **Mined real pairs (primary — the validation ground truth).** The same
  paragraph's AI-drafted version and its accepted rewrite. Because both
  sides share content, this is the one data source that controls for the
  genre/topic confound flagged above — it isolates style, not subject
  matter. Concrete, low-effort sources already sitting in existing harness
  state:
  - Claude Code session transcripts already log every draft-then-revise
    turn; any paragraph the author substantially rewrote from a Claude
    draft is a natural (negative, positive) pair, at no new authoring cost.
  - Paper repos' own revision history (git log on manuscript files), and
    `ingest-decision-letter`'s remark ledger where a reviewer flagged prose
    that was then rewritten.
  - Open problem, not yet solved: identifying *which* commit is "the AI
    draft" vs. "the accepted version" needs a reliable heuristic (e.g.
    first Claude-authored version in a session vs. the final commit before
    submission) — this is real design work, not a detail to wave past.
- **Synthetic de-idiosyncratization (secondary — training augmentation
  only).** Run the author's own voiced paragraphs through several different
  models to produce flattened/generic rewrites. Cheap, unlimited volume,
  and varying models avoids overfitting the negative class to one model's
  specific tics. But a deliberately-flattened rewrite risks being an easy
  strawman — more distinguishable than naturally-occurring drift — which
  would inflate apparent accuracy without real signal.

**Rule**: synthetic pairs may enlarge the training/reference set, but the
Validation gate's reported accuracy is measured on held-out **mined** pairs
only. A detector that only ever proved itself against its own synthetic
negatives has proven nothing — the same "unvalidated premise stacked on
itself" trap the panel already flagged once.

## Candidate extensions (not committed — reference only)

These are described so the vision doesn't need re-deriving later, but each
carries its own open questions the panel raised, and none is scheduled:

- **Perplexity/burstiness scoring** under a reference LM (local-first: an
  open-weight local model, later a personal finetune; OpenRouter only as an
  occasional independent cross-check, never the primary loop, given
  inconsistent per-provider logprob support and cost). Inherits the same
  detector fragility as above.
- **Drift tracking** — trend lines per chapter/section, keyed by
  `(commit, file, paragraph-id)`. Needs a stable paragraph-identity scheme
  first (content-hash plus fuzzy match across edits/reorderings — the same
  problem `latexdiff`/track-changes tooling already solves), not yet
  designed. Likely belongs in a standalone report skill (in the shape of
  `trace-doctor`/`nightbeat-report`), not folded into a per-PR panel, since
  it outlives any single PR's fork-context run.
- **Paraphrase-invariance probe** — round-trip a paragraph through
  paraphrase/back-translation; idiosyncratic prose changes more than
  boilerplate under round-tripping. Run on demand given round-trip cost.
- **Finetuned personal model** — gated on the user-tier corpus being mature
  (it doubles as training data). Two roles if built: scorer (replaces the
  interim local model in perplexity scoring) and generator (style-transfer
  rewrite assistant — a different, later goal than flagging). **Storage
  boundary, decided now regardless of build order: the checkpoint is
  local-only and never uploaded to, or served via, any hosted inference
  provider** — a model finetuned on one person's prose is itself a
  stylometric fingerprint and an impersonation risk if it or its outputs
  leak.
- **Multi-model variance / ensembling** — disagreement-as-signal across
  independent model families, cross-model calibration, sampling policy.
  Explicitly the least mature idea in this document: no evidence yet that
  ensemble variance tracks human-perceived voice fidelity at all. Not worth
  designing further until v1's single-model signal is itself validated.

## Quality-uplift (deferred — separate tracking, not this document)

Scoring against "how leading journals write" is a distinct goal from voice
fidelity (sound like yourself vs. write better), and the two risk blending
at the synthesis step even with careful tagging discipline. Track as its own
vision note if pursued; it does not share v1's corpus, auditor, or gate.

## Data egress — explicit statement

- **Default is local-only.** Stylometric scoring (dependency-free baseline
  or a local library) runs entirely on-machine; nothing leaves by default.
- **OpenRouter cross-check (candidate extension, not v1, opt-in per
  project — see Candidate extensions -> Perplexity/burstiness scoring for
  why it is occasional-only)**: sends manuscript paragraph text to a
  third-party API aggregator. Before this is ever enabled, state the
  upstream provider's retention/training-use policy for the specific model
  used, and treat pre-publication manuscript text as confidential by
  default — this is not a decision to make implicitly by turning the
  feature on.
- **LLM qualitative auditor** already sends manuscript text to whichever
  model runs it (Claude, currently) — no different from the existing
  `review-pr-prose` panel's status quo, stated here for completeness rather
  than as a new exposure.
- **Finetuned model artifact**: local-only per the storage boundary above.

## Retention

Stored corpus entries are derived data (see Corpus storage), not a system of
record — no indefinite-accumulation assumption. A periodic review pass
(mirroring `edm.md`'s sync/purge discipline) should be able to remove or
down-weight retracted, embargoed, or simply outdated entries; this is a
requirement to design into the extraction/storage step when it's built, not
an afterthought.

## Interface

If the gate passes: extend `review-pr-prose`'s panel with the two v1
layers, matching the existing AI-tells auditor pattern. Also expose the
stylometric pre-filter standalone for mid-draft checks outside a PR cycle.
Nothing beyond v1 has an interface decision yet.

## Open questions carried forward

- Whether v1's simplest signal (stylometric distance) actually agrees with
  the author's judgment — the entire premise, resolved only by running the
  validation gate.
- Library selection for the pre-filter, if a library ever beats the
  dependency-free baseline — deferred, including checking French-language
  coverage, which most candidate packages do not advertise.
- Whether project/harness/manuscript tiers are ever needed, or whether a
  single user-tier corpus suffices indefinitely for a one-author tool.
- How to reliably identify "AI-drafted version" vs. "accepted rewrite" when
  mining real pairs from session transcripts and revision history — no
  heuristic proposed yet, only the requirement that one exists before mining
  starts.
- How to distinguish a dismiss that means "this really is my voice" from one
  that means "I am tired of this flag" — both feed back to the corpus as
  "confirmed voice," so nothing currently separates genuine in-voice prose
  from reviewer friction. Unsolved; the homogenization countermeasure leans
  on this distinction it does not yet have.
