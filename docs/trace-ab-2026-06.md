# Trace phase-5 A/B pre-registration — 2026-06 (ticket 0315, trace-doctor phase 5)

**Shadow dollars**: every $ below is a list-price API-equivalent under
subscription auth — capacity consumption (rate limits, context budget), never
invoiced money. Baselines carry over from the phase-4 counterfactual accounting
(`docs/trace-counterfactuals-2026-06.md`).

This document is the **pre-registration** for the two phase-5 A/B measures
routed by phase 4. It is committed **before any B-arm data exists**, so git
history proves the ordering (interventions and decision rule fixed first, data
second). The live arms and the verdicts stay on ticket 0245; this ticket (0315)
lands the interventions, metrics, windows, exclusions, and the decision rule.

## Pinned interventions

One intervention per measure, confirming 0245's Action-1 defaults.

### Measure A — model right-sizing of long Opus mains

**Intervention**: paired replay. Re-run ~5 closed tickets from their original
base SHA through the same skill path with a **Sonnet main** (instead of the
original Opus main), and compare each replay against its original Opus trace on
two axes: total shadow-$ spent, and whether the fresh PR passes `/gaze`. Paired
same-ticket comparison beats a week-vs-week contrast for a model change that
would otherwise put a whole nightbeat week at risk.

The **procedure** is pinned here; the **sample selection** (which ~5 closed
tickets) is deferred to 0245, chosen at replay time from the closed-ticket
corpus. No calendar window applies — measure A is ticket-keyed, not
time-windowed.

### Measure B — verification convergence

**Intervention**: caller-level convergence. After a PR already carries one
completed full `/gaze` round, a repeat **caller-level** `/gaze` invocation on
the same PR runs phase 6 (verify-gate) only — no phases 2–5 panel re-run.

Surface decision (important — see the measurement-window rationale below): the
flag governs **caller-level re-invocation** of `/gaze` on an already-reviewed
PR, *not* the internal round-1 REROLL re-entry branch inside `skills/gaze/`.
The internal branch is already gate-only and was live and unchanged during the
June measurement window; the $259/wk `vg` bucket that phase 4 flagged is
measured from **caller-level repeat invocations** of the full `/gaze` on the
same PR (turns after the 2nd verify/gaze invocation). Instrumenting the
internal branch would move a surface the baseline never charged; instrumenting
the caller-level re-run is exactly what the `vg` bucket counts. The flag ships
default off (current practice), so live behaviour is unchanged until the B-arm
week flips it on — see `skills/gaze/telemetry.yml` (`convergence.enabled`,
env override `GAZE_CONVERGENCE_ENABLED`).

## Metric definitions

All metrics are computed by the committed scripts (`scripts/trace-stats.py`,
`scripts/trace-hypotheses.py`, `scripts/trace-pr-join.py`) over cached inputs,
reproducibly, without network.

- **`cost_per_merged_pr`** — total shadow-$ in the arm divided by merged PR
  count. Primary cost metric.
- **`cost_per_cycle`** — total shadow-$ divided by gaze/verify cycle count.
  Secondary cost metric for measure B (convergence changes cycles, not PRs).
- **`reroll_per_pr`** — REROLL mentions per PR. Guardrail. Baseline **33/112**.
- **`escalate_count`** — ESCALATE mentions in the window. Guardrail. Baseline
  **18**.
- **`gaze_verdict_distribution`** — counts of APPROVED / REROLL / ESCALATE
  gaze verdicts. Reported for context.

**Explicitly excluded metric**: merged-rate. It is saturated at 112/112 = 100%
in the phase-4 corpus, so it carries no discriminating signal and is not a
guardrail here (per the phase-4 routing decision).

## Windows

- **Measure A**: ticket-keyed, **no calendar window**. Each replay is paired to
  its original ticket's trace; the comparison unit is the ticket, not a date
  range. `filter_window` does not apply to arm A.
- **Measure B**: two **disjoint weeks**, one control (flag off) and one
  treatment (flag on), fixed at B-arm launch **before any data is collected**.
  <!-- TODO(0245): pin the two disjoint week date ranges here at B-arm launch,
       before collecting any B-arm data. Do not fabricate dates ahead of the
       run. -->

## Exclusion rules

- **Study-session reflexivity**: sessions whose work *is* this trace-doctor
  study (the phase-4/5 measurement sessions themselves) are excluded from both
  arms, per the counterfactuals doc — a study session's spend is not
  representative production work and would contaminate the arm it measures.

## Decision rule

Implemented as a pure function in `scripts/trace_ab_decision.py` (`decide`),
unit-tested red-first in `tests/test_trace_ab_decision.py`:

> **Adopt** the candidate config **iff** its cost is strictly below baseline
> (`cost_per_merged_pr` for the primary comparison) **AND** each guardrail
> (`reroll_per_pr`, `escalate_count`) stays **at or below**
> `baseline * (1 + noise)`. Otherwise **reject**.

- **Noise band**: pre-registered at **10%** (`guardrail_noise_pct = 0.10`). The
  band is inclusive (`<=`): a guardrail exactly at `baseline * 1.10` still
  adopts; any excess rejects.
- The guardrail is **binding**: a cost win with a breached guardrail is a
  REJECT. No post-hoc metric shopping — verdicts come only from the metrics
  defined above.

Per-window guardrail metrics are sliced with `filter_window(rows, start, end)`
(ISO-date inclusive on both ends) before the decision is computed for measure
B's two weeks.
