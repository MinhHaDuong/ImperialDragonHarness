# Trace hypothesis-testing report — 2026-06 (ticket 0243, trace-doctor phase 3)

Confirmation pass: the thirteen hypotheses fixed by phase 2b
(`docs/trace-open-coding-2026-06.md`) computed over the FULL 28-day
census — 1,790 agents, 309 sessions, $6,705 total (≈ $1,676/week). The
30-trace discovery sample played no part in any number below.

## Method

- Census regenerated with the new 0243 detector columns:
  `uv run python scripts/trace-stats.py --days 28 --output <csv>`
  (nav/idle turn classification, merge-success marker, verify/gaze count).
- Statistics: `uv run python scripts/trace-hypotheses.py --census <csv>
  --compact-audit-json <json>`; H8 input from
  `scripts/trace-compact-audit.py --days 28 --json`.
- $ attributions for H10/H11 are linear per-turn approximations
  (cost × turns-in-class / turns). Late turns read more context than
  early ones, so H10 is a LOWER bound; H11's idle-turn component counts
  legitimate reasoning/communication turns too and is an UPPER bound.
  Both are screening numbers — phase 4 settles them counterfactually.
- Zero LLM tokens; aggregates only.

## Verdicts

| ID | Hypothesis | Statistic (28-day census) | Verdict |
|----|-----------|---------------------------|---------|
| H1 | cache_read dominates $ | 68.7% of categorized $ ($4,252 of $6,189) | **Supported** |
| H2 | top-decile context concentration | cr/turn by cost decile: 24K (d1) → 161K (d10), 6.8×; log-log exponent 1.18 | **Supported** (as reframed; the quadratic form stays rejected) |
| H3 | read-only agents drift past budget | 68 agents, $96, 1.4% of spend | **Confirmed-but-small** — deprioritize |
| H4 | gaze cost independent of diff size | needs forge join (`--pr-stats`) | **Needs-data** → phase 4 |
| H5 | spawn-boundary redundancy | subagent cache_write ≤ $572 upper; per-message overlap needs phase-4 extraction | **Plausible, needs-data** |
| H6 | mains are the cost center | 75.4% of $ from main agents | **Supported** |
| H7 | Opus mains sit off the cost curve | mean log-residual, mains: opus **+1.04** (≈2.8× over curve), sonnet +0.00, haiku −0.55 | **Supported** |
| H8 | compaction late or absent | 64 missed runs, **$1,044** recoverable (upper bound), 135 compactions observed | **Supported** |
| H10 | post-delivery tail is material | 60 sessions carry a merge marker; tail = **$968**, 14.4% of all spend (lower bound) | **Supported** — largest surprise |
| H11 | micro-turn churn | nav+idle turns ≈ **$2,169**, 32.4% (upper bound; idle includes legitimate reasoning turns); p99 nav-run length 32 | **Supported as screening** — needs phase-4 tightening |
| H12 | same-file re-reads | 384 agents re-read one file ≥3×; they hold $4,679 (total agent $, NOT the waste itself) | **Weakly supported** — statistic too blunt, refine in phase 4 |
| H13 | verification re-entry | 43 sessions invoked verify/gaze ≥2×; they hold $2,080 (31% of spend; incremental cost not yet isolated) | **Supported as signal** — incremental $ in phase 4 |
| D1 | zero-turn traces | 29 flagged, excluded from all $ statistics | **Done** (chore) |

## Ranked recommendations (by $/week at stake)

Window total ≈ $1,676/week. "At stake" is the screening bound above, not
a promised saving; the Route column says which phase settles it.

| # | Recommendation | $/week at stake | Bound | Route |
|---|----------------|-----------------|-------|-------|
| 1 | Micro-turn discipline: batch navigational commands, cap nav runs (p99 run = 32 turns) | ≤ $542 | upper | Phase 4: re-estimate excluding final/communication turns, then prompt-rule A/B |
| 2 | Verification re-entry: make gaze/verify converge in one pass | ≤ $520 (total in affected sessions) | upper | Phase 4: isolate incremental $ of 2nd+ invocations |
| 3 | Compaction policy: compact/clear when cr/turn stays ≥300K over 30+ turns | ≤ $261 | upper | Adopt cheaply: the phase-2a detector IS the counterfactual; wire as advisory check |
| 4 | Post-delivery tail: move wrap-up (memory, housekeeping, roar) to a fresh cheap session instead of the peak-context session | ≥ $242 | lower | Phase 5 A/B: roar-in-fresh-session flag |
| 5 | Model right-sizing: long interactive mains on Opus run ≈2.8× over the cost curve | (subset of H6's 75%) | — | Phase 5 A/B: default long autonomous mains to Sonnet, measure quality via gaze verdicts |
| 6 | Read-only drift caps (H3) | ~$24 | exact | **Reject**: measured small; close the seed |

Quality baseline (trace → PR outcome join) and H4 remain open pending the
forge join; phase 4 should land `--pr-stats` first so recommendations 1–5
can each carry a quality-risk column before any A/B ships.

## Phase-4 feedstock

- Tighten H11: classify idle turns into reasoning-before-action vs
  trailing communication; exclude the final turn.
- H13 incremental cost: per-invocation $ delta within re-entry sessions.
- H12 refine: re-read cost = (repeats−1) × file size × cache_read rate,
  not total agent $.
- H5 extraction: per-message cache_creation overlap across siblings
  (needs trace-level pass, still zero-LLM).
- H4 + quality: forge CLI join (PR number from trace → diff size,
  verdict, REROLL count) cached to a committed CSV.
