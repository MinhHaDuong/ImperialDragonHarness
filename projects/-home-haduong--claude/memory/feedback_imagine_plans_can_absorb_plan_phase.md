---
name: imagine-plans-can-absorb-plan-phase
description: Raid Phase 3 (Plan) is redundant when Phase 2 Imagine prompts demand file:line-precise structured output — verified 5/5 PRs approved in the 0252 raid
metadata:
  type: feedback
---

In the 2026-07-13 raid on the 0252 family, the Phase 2 Imagine agents were
prompted for a fixed structure (SCOPE / SIMPLEST PATH with exact file paths /
REUSE with file:line refs / ANTIPATTERN HITS / DRIFT / RISKS). Their reports
came back plan-grade — numbered steps, verified anchors, test-first framing —
so Phase 3 (Plan) was skipped and the reports fed the execute prompts
directly. All five PRs passed gaze (each with exactly one substantive
REROLL, none traceable to missing plan detail).

**Why:** a separate Plan pass over an already file:line-precise Imagine
report mostly restates it; the token cost of four extra sonnet agents bought
nothing the feasibility cross-check (Phase 4) did not already verify.

**How to apply:** when writing raid Imagine prompts, demand the structured
plan-grade format up front (exact paths, line refs, first test, reuse
anchors); then collapse Phase 3 unless a ticket's Imagine report comes back
vague or the drift guard flags it. Keep Phase 4 (mechanical anchor checks +
cross-ticket conflict scan) — that is the pass that catches what Imagine
gets wrong, e.g. the [[feedback_rebase_drop_cascade]] registry class.
