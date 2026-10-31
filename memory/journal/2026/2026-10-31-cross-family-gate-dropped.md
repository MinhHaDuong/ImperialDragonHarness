# Cross-family gate dropped; family becomes a routing preference (2026-10-31)

Context: interactive session on padme (claude-opus-5-5). It started from the
author's question "is local Qwen a reviewer?" and ended with three merges: PR 2065,
PR 2066 and PR 2085.

Events:
- The reviewers skill named "llama.cpp on Padmé". The author corrected it: the
  Padmé LLM service is configurable. Qwen 3.8 Flash Next on strata is the default,
  Nemotron 74B on llama.cpp and Gemma are alternatives, on one or two GPUs, and
  the lineup changes within days. PR 2065 now names the service only.
- A dry run showed that `review_notes.py gate --require-cross-family` accepted a
  seat stamped `Local`, while `review_evidence.py record --family Local` refused
  it. PR 2066 added `local` to FAMILIES. Its review (self plus an OpenAI seat)
  found that a `Local` seat counted as cross-family against any producer: for
  example Qwen-padme against a Qwen-OpenRouter producer, or Gemma-padme against
  Gemma-Albert.
- Two designs were proposed and rejected by the author: a fixed list of
  families Padmé never serves, and a four-child tracker separating model
  identity (family, model, quant) from access (runtime, provider, engine,
  compute). The author's rulings:
  - model and access are distinct, and no field is assumed useful or known;
  - the cross-family benefit is unmeasured;
  - spend, locality, the hour and night versus interactive runs weigh as well;
  - a gate failing on an unknown family is too strong;
  - "Une bonne barrière est une barrière supprimée."
- Measure (Sonnet subagent, read-only, 212 attribution records): in mixed
  panels, other-family seats get +0.28 adopted findings per seat (95% interval
  +0.11 to +0.45). This is confounded with seat angle and risk selection.
  Recorded in `conception/research/2026-10-31-cross-family-seat-measure.md`.
- PR 2085 removed `--require-cross-family`, `cross_family_seats`, and the
  plan-write consent refusal with `--no-cross-family` and `--home-family`.
  decorrelation.md now lists family among routing criteria. Kept: spend
  consent, the family field on seat lines, the self-only refusal, and the
  "never called independent" wording.
- On PR 2085's fix round (a same-family seat only), main's verify-gate refused
  admission with "no cross-family seat", applying the rule the PR removes. A
  re-gaze with an OpenAI seat (gpt-6.1-sol) cleared it, then APPROVED round 1.
- `raid_land.py` warned on all three merges that the attribution block could
  not be rendered into the PR body (fact order on 2065 and 2066, writer not
  derivable on 2085). Capture from notes succeeded for all three.

Outcome: merged at 7d546daf (2065), d704081a (2066) and 95ede53f (2085).
Attribution records are in `memory/evidence/attribution/2026-10-31-review-attribution-pr20{65,66,85}.md`.
