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

The **procedure** is pinned here; the **sample** is pre-registered below
(§ Measure A — replay sample, ticket 0326) by a deterministic rule, before any
replay runs. No calendar window applies — measure A is ticket-keyed, not
time-windowed.

### Measure A — replay sample (pre-registered, ticket 0326)

**Selection rule** (deterministic, applied once, before any replay): take the
**5 most recently closed tickets** — ordered by their `closed` log timestamp,
strictly **before 2026-07-14T00:00Z** — whose merge PR carries a verify-gate
**APPROVED** verdict, **excluding** trace-doctor study-session tickets per the
reflexivity rule below. A ticket whose PR merged without an APPROVED verdict
(tracker-close, doc-only, fast-tracked) does not qualify; the APPROVED filter is
what makes the sample a fair test of Opus-main delivery quality.

Resolved sample (ticket → merge PR → replay base SHA, the forge-recorded base
that equals `git merge-base` of the PR's two parents):

| Ticket | PR | Replay base SHA | Title |
|--------|-----|-----------------|-------|
| 0217 | #564 | `b34c5fe2dfa55a8c3fc710f4089a29cd6b74c469` | OS-network-isolate the reviewer seat-runner |
| 0319 | #563 | `b34c5fe2dfa55a8c3fc710f4089a29cd6b74c469` | carry resolve-$$-to-literal caveat into workflow.md |
| 0318 | #562 | `b34c5fe2dfa55a8c3fc710f4089a29cd6b74c469` | harden worktree-path guard to a blocking deny |
| 0317 | #561 | `b34c5fe2dfa55a8c3fc710f4089a29cd6b74c469` | close nested-repo escape in parked-cwd guard |
| 0291 | #550 | `ffd4d3cd23aa74b420c78b8a5fbf433c74f367eb` | shared root-cause taxonomy for verify-gate/skill-doctor |

Skipped by the rule between the qualifying five: 0324/#567 and 0257/#552 and
0266/#556 (no APPROVED verdict on the merge PR); 0316/#553 and 0315/#33
(trace-doctor study sessions, reflexivity-excluded — see § Exclusion rules).
Four of the five share base `b34c5fe` (a same-evening merge wave); each replay
still checks out its own recorded base.

### Measure A — replay runbook

One paired replay per sampled ticket. The operator drives this manually — no
framework, no orchestrator. For sampled ticket `T` with replay base `SHA`:

1. **Checkout the base.** `git -C <primary> worktree add .claude/worktrees/replay-T <SHA>` (or a
   fresh clone at `SHA`) — the same tree the original session started from.
2. **Pin a Sonnet main.** Launch the replay with the main agent on **Sonnet**
   (per-invocation `model` override, e.g. `claude --model sonnet -p "/hunt T"`),
   not the session-default Opus. Subagents keep their normal per-role models.
3. **Same skill path.** Run the identical skill sequence the original used —
   `hunt` → implement → `gaze` → verify-gate — producing a fresh PR.
4. **Record the arm.** Run the trace census over the replay session
   (`scripts/trace-stats.py --output <replay-census.csv>`) and refresh the join
   over the fresh PR (`scripts/trace-pr-join.py`, online step, one-time).
5. **Harvest offline.** Pair the replay census (candidate) against the original
   ticket's census slice (baseline) through the new CLI:
   `scripts/trace_ab_harvest.py --baseline-census <orig.csv> --candidate-census <replay.csv> --json`.
   No `--window` (measure A is ticket-keyed). The CLI computes
   `cost_per_merged_pr`, `reroll_per_pr`, `escalate_count` and routes them
   through the pre-registered `decide()`. The verdict per ticket is: Sonnet
   adopted iff its shadow-$ is below Opus's **and** the fresh PR passed `/gaze`
   **and** guardrails held within the 10% band.

The aggregate measure-A verdict (adopt/reject across the five) is written on
**ticket 0245** after the replays run, not here — this document pre-registers
the sample and procedure only.

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

- **Cost key**: `decide()` compares on `cost_key`, defaulting to
  `cost_per_merged_pr` (measure A). Measure B passes `cost_key="cost_per_cycle"`,
  since convergence changes cycles, not merged-PR count. These are the exact
  dict keys the metric definitions above name — the harvest step reads this doc
  and builds those keys.
- **Noise band**: pre-registered at **10%**, exported as the module constant
  `PREREGISTERED_NOISE_PCT` and used as the `decide()` default; the harvest step
  uses this value, not an ad-hoc override. The band is inclusive (`<=`): a
  guardrail exactly at `baseline * 1.10` still adopts; any excess rejects.
- The guardrail is **binding**: a cost win with a breached guardrail is a
  REJECT. No post-hoc metric shopping — verdicts come only from the metrics
  defined above.

Per-window guardrail metrics are sliced with `filter_window(rows, start, end)`
(ISO-date inclusive on both ends) before the decision is computed for measure
B's two weeks.
