# Trace counterfactual accounting — 2026-06 (ticket 0244, trace-doctor phase 4)

**Shadow dollars**: every $ below is a list-price API-equivalent under
subscription auth — capacity consumption (rate limits, context budget),
never invoiced money. Window: 28 days, 1,795 agents, 309 sessions,
$6,768 total (≈ $1,692/week).

## Method

- Census regenerated with disjoint per-turn buckets: each turn's
  cache_read is attributed to exactly ONE bucket, priority **tail**
  (after the LAST merge marker) > **vg** (after the 2nd verify/gaze
  invocation) > **micro** (navigational/idle, never the final turn) >
  core. Sums are exact attributions, not linear shares; the addressable
  total is a sum by construction.
- H10 premium = tail cache_read − (tail turns × 15K fresh-session
  baseline), per family pricing, floored per agent.
- Forge join: `scripts/trace-pr-join.py`, 117 (repo, PR) pairs from
  merge markers, 112 resolved (5 unresolved, listed blank in the cache:
  -claude-projects 67/366, git-erg 309, padme 321/322); cache committed at
  `docs/trace-pr-join-2026-06.csv`; blank rows excluded from merged-rate
  denominator and diff accumulation, reported separately as `unresolved_prs`.
- Reflexivity sensitivity: sessions whose merge markers cite the
  study's own PRs are recomputed out.
- Open-coding prose is cited nowhere below; every number is computed.

## Settled numbers (screening → refined)

| Probe | Phase-3 screening | Phase-4 refined | What changed |
|---|---|---|---|
| H10 post-delivery tail | $968 (14.4%) | **tail $247; relocation premium $227** (~$57/wk); mandated work = 8.3% of tail turns | First-marker confound removed (last-marker segmentation): ~4× inflation confirmed — the author's challenge was right |
| H11 micro-turns | ≤$2,169 (32%) | **$1,071** (~$268/wk), exact attribution, final turns excluded | Halved; remains the largest bucket |
| H13 verification re-entry | $2,080 (sessions' total) | **$1,038** (~$259/wk) incremental-upper (turns after 2nd invocation), 44 sessions | Halved; difficulty conditioning below |
| H12 same-file re-reads | "$4,679 at stake" | **$3.04 upper** (excess reads × 2K tokens × family rate) | Dissolves — cache pricing makes re-reads near-free |
| H5 spawn preambles | ≤$498 | **$129 upper** (subagent first-turn cache_writes) | Shrinks; per-message overlap analysis no longer worth building |
| Dedup addressable total | (not summable) | **$2,356 = 34.8%** of all spend (tail+vg+micro, disjoint) | Exact; overlaps H8's counterfactual, so do not add H8 on top |
| Reflexivity | — | 2 study sessions in window; excluding them moves micro by −$5.6, tail by −$7.3 | Negligible this window (most study sessions post-date the census cutoff — recheck next month) |
| H2 segmented | pooled 24K→161K | mains 42K→217K (5.1×), subagents 24K→96K (4.1×) | Concentration holds in BOTH segments — no Simpson artifact |

## Forge join: H4 and the quality baseline

- 33 sessions joined to PRs; **112 resolved of 117 pairs (5 unresolved,
  listed blank in the cache); merged rate 112/112 = 100%**; 33 REROLL
  mentions, 18 ESCALATE mentions. Merged-rate is saturated at 100%, so
  the operative phase-5 guardrail metric is REROLL mentions/PR (33 over
  112) and ESCALATE mentions (18), not merged-rate.
- **H4 (gaze cost vs diff size)**: re-entry sessions' median joined diff
  is **465 lines vs 597** for single-pass sessions — re-entry is NOT
  explained by bigger diffs. Combined with phase 3's finding that the
  one gaze-entry top-5 session cost $254, the evidence leans toward
  verification cost being decoupled from diff size, but 33 joined
  sessions is thin; treat as supported-weakly.
- **H13 difficulty conditioning**: same comparison — re-entry sessions
  do not carry larger diffs, so the $1,038 vg bucket is not explained
  away by task difficulty. It still contains legitimate round-2 fix
  work (gaze REROLL loops); the A/B below is what separates process
  cost from fix cost.

## Routing (the phase-3 recommendation list, settled)

| # | Recommendation | Refined $/wk | Routing |
|---|----------------|--------------|---------|
| 1 | Micro-turn discipline (batch navigation, no idle-turn chains) | $268 exact | **Adopt now**: prompt-rule in workflow.md (batch read-only git/cd into one compound; no consecutive single-nav turns). Cheap, no quality risk; re-measure next census |
| 2 | Verification convergence (gaze/verify single-pass) | $259 upper | **Phase-5 A/B (shortlist)**: not explained by difficulty; measure REROLL/PR (33/112) and ESCALATE (18) as guardrail |
| 3 | Compaction policy | ≤$261 (H8 upper; overlaps buckets) | **Adopt as advisory**: wire `trace-compact-audit.py` into the monthly trace-doctor run; no separate A/B |
| 4 | Post-delivery tail relocation | $57 premium | **Reject the fresh-session mechanism** — premium too small for the machinery; compact-before-wrap-up (covered by #3) captures most of it |
| 5 | Model right-sizing of long Opus mains | unresolved by accounting | **Phase-5 A/B (shortlist)**: largest unresolved lever (mains = 75% of spend, Opus +1.04 off-curve); quality measured via gaze verdicts |
| 6 | Read-only drift caps (H3) | $24 | **Rejected** (phase 3, unchanged) |
| 7 | Re-read dedup (H12) | $0.7 | **Rejected** — dissolved by refined accounting |
| 8 | Spawn-preamble dedup (H5) | $32 upper | **Rejected** — bound too small to pursue |

**Phase-5 shortlist (the 1–2 measures accounting cannot settle):**
model right-sizing of long mains, and verification convergence. Both
need live A/B because their cost is entangled with delivery quality;
both carry REROLL mentions/PR (33/112) and ESCALATE mentions (18) as
the operative guardrail metrics (merged-rate is saturated at 100%).

## What accounting could not settle, and why

- Whether vg-bucket spend buys quality (REROLL fixes are real fixes) —
  needs the A/B, not traces.
- Whether Sonnet mains deliver gaze-APPROVED PRs at Opus rates — the
  census never observes the counterfactual model.
- H4 beyond medians — 34 joined sessions is too thin for a regression;
  the join cache will accumulate across monthly runs.
