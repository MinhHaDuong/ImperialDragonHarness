# Raid on ticket 0902 — gaze risk band — PR #1155

2026-10-03 (run 2026-10-02 22:00 → 2026-10-03 02:05, +0200). Harness checkout.
Autonomous `/raid 902` on the pi runtime — first full raid cycle
(hunt → /gaze → merge) executed end-to-end on this runtime; all Claude-Code-shaped
skill contracts (subagent fan-out, /review, /simplify, built-in agents) adapted
to pi's named-agent model (planner/reviewer/scout/worker, local 27B).

## Context

Ticket 0902: "gaze tiers on diff size, never on which paths the diff touches".
Add a `--risk` band mode (high/low/normal from path patterns) to
`scripts/prose_predicate.py`, combine the band with the size tier in /gaze
phase 1 (high raises one rung, clamped at full; low lowers one rung, floored at
tiny; the battery never drops below Agent A + Agent C + phase-6 gate), and state
in the skill text that size and risk are two axes.

## Observable events

- Phases 1–5 (select, imagine, plan, feasibility, execute): single named
  ticket; blind-spot pass adopted 4 findings (notably: `--risk` must NOT inherit
  the missing-path refusal — the anchor roster lists deleted/renamed paths
  absent at HEAD; and the R9 fork-blocking launch-paragraph ratchet forbids the
  word "parallel" in new doctrine text, so S1 uses "concurrently"). Executor
  opened PR #1155 (`t0902-gaze-risk-band`) with red-first tests (T0–T4 red at
  the test commit, green after the code commit).
- M1 Part 2 population replay (orchestrator, post-PR): window 2026-09-23 →
  2026-10-02 (9/14 days); population = 2 PRs (#1131 583/5 full+high → full
  clamped; #1132 269/7 full+normal → full); raised 0, lowered 0, floor
  invariant holds; shape comparison #812 shape (A+B+5+/simplify+gate) >
  #177 shape (A+1+gate). Report appended to the PR body.
- /gaze phase 1: tier = full (292 lines / 5 files > panel-width 30/2; pipeline
  paths present). Phase 2–4: 6 internal seats — seat B + 5 perspectives
  (correctness, consistency, scope, red-team, doc-propagation), all
  approve/high — plus the external panel (openrouter-frontier ran: findings=0,
  approve; openrouter-budget SEAT-FAILED, the ticket-0347 reasoning-field hang
  class, fail-open).
- The doc-propagation seat found two `verifiable:` minors, both confirmed
  against the diff: (1) the module docstring at prose_predicate.py:43 called
  the high set "the repo's existing dangerous-path registry" while
  RISK_HIGH_GLOBS is registry + `hooks/**` + `settings*.json`; (2) the sentence
  "the 15+ files un-reviewable breaker is checked before the band" was false
  under the text's own top-to-bottom layout (the band-combine block precedes
  the breaker bullet).
- Gate round 1: REROLL, forced by the two unresolved `verifiable:` minors
  (all three exit criteria ADDRESSED with commit+file:line evidence; no scope
  overflow; the fix commit that landed between posting and gating touched
  neither cited spot). /simplify (adapted) applied 4 trims (commit 88d84a5f).
  Fix agent round 1: red→green ratchet update — T1's asserted phrase changed
  from "checked before the band" to "never sets a battery tier" (red), then the
  SKILL.md sentence reworded to "the breaker pre-empts the band — its ESCALATE
  fires before any battery spawns" and the docstring parenthetical corrected
  (green) — commit 36f52429. Gate round 2: APPROVED (both defects
  defect-verified at the tip; one new `consider:` residual — the T1 function
  docstring still says "checked before the band", non-asserted, does not bounce).
- Merged as c65d2284 (2026-10-03T00:18:23Z); ticket 0902 autoclosed and
  archived by erg-pr-merge. `make check` on main after merge: 1350 passed,
  2 skipped — identical to the pre-merge baseline (both skips pre-existing
  environment skips).
- Telemetry: wall 11694 s (195 min) from /gaze phase 1 to verdict, versus the
  1800 s escalate threshold in `skills/gaze/telemetry.yml`. Disclosed in the
  verdict comment at the terminal boundary rather than stopped (the run had
  already reached its verdict; every phase progressed, no fork-liveness window
  expired). Cause: the six-seat parallel fan-out on the local 27B model — last
  seat artifact at T+111 min; seat artifacts landed 22:53→00:44.

## Decisions already made

- `--risk` does not inherit the missing-path refusal (pure path-pattern match,
  no disk read; proven by T0 with fixture files never created on disk).
- High set = `pipeline_paths` registry + `hooks/**` + `settings*.json` as named
  constants (dependency direction: the predicate does not read panel-width.json);
  one-directional registry-coverage ratchet (0901 pattern).
- Low set = `docs/**`, `*.bib`, `**/fixtures/**`; low requires every file low.
- Combination: round-1 only; `review:standard` pre-empts; battery floor
  Agent A + Agent C + phase-6 gate at every tier and band.
- S1 text avoids "parallel" (R9) and any literal `pr_files >= N` (keeps the
  unreviewable-breaker regex bound to the breaker bullet).
- The external-panel SEAT-FAILED / PANEL-INTEGRITY lines were carried verbatim
  into the verdict comment and not dispositioned as findings.

## References

- PR #1155 (merged, c65d2284) — panel review, verdict comment, M1 Part 2 report.
- tickets/closed/0902-gaze-tiers-on-diff-size-never-on-which-p.erg.
- scripts/prose_predicate.py (RISK_HIGH_GLOBS, RISK_LOW_GLOBS, risk_band,
  --risk); skills/gaze/SKILL.md § 1. Setup (band block, breaker sentence).
- tests: test_prose_predicate_cli.py (T0), test_verify_fork_contracts.py
  (T1/T2), test_gaze_prose_routing.py (T3/T4).
- Raid annotation checkpoints on local branch `raid-0902-annotations`
  (206d4924, b0fb22fa, 355e992d, 4ff298f9) — unmerged by design (process
  record, not content).
