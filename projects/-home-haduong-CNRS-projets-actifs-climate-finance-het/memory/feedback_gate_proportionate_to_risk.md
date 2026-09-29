---
name: feedback_gate_proportionate_to_risk
description: "Size the merge gate to the PR's risk — full /gaze cost ~75 min and ~1M tokens on one data PR; a checklist review does it in ~15 min"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 36288e08-760c-498d-809d-4ea0d872d521
  modified: 2026-09-29T16:01:33.401Z
---

Size the merge gate to the risk, and never resume a fat executor for a small fix.

- Data-migration PR: one time-boxed (~15 min) checklist review agent in its own worktree — reproduce byte identity of served views, determinism (two builds), validator mutations rejected with named reasons, counts, exit criteria, check-fast + lint once — then merge. Measured 2026-09-23: 0873's checklist review took 11 min; full /gaze on 0872 took ~75 min, 9 agents, ~1M tokens, then idled retrying `reviewers scorecard` and never returned.
- Presentation or small follow-up PR: a proportionate check by the orchestrator (targeted grep/render probes, data/ diff scope), gate evidence posted as a PR comment.
- Small edits (a column width, a count fix): a fresh small agent or do it inline. Resuming the executor that carried seven batches (≈560k tokens of context) cost 25 min for one CSS change.

- Docs-only or prose PR (2026-09-29, REL protocol): no raw `pytest` and no whole fast tier. The tests were split by workpackage so they are not all rerun each time, and the fast tier must resolve in about 10 s, "especially for a PR without code". Use the check that can break: relative-link check of the touched files, the adherence tier once, the Makefile WP target only when code changes. The author interrupted my full `make check-fast` twice; a branch `t1700-file-check-fast-10s` was merged the same day (not read).

**Why:** the author called both out the same day ("25 min to fix a column width", "you will use gaze, the fat executor, in the same breath", "that gaze has been running for hours").

**How to apply:** state the gate tier in the plan before launching; relates to [[feedback_agent_briefs_scoped_gates]] and [[feedback_helper_agent_needs_own_worktree]].

- Ticket 1700 measurement (padme, 2026-09-29): `make check-fast` took 89.56 s before two real-data JETP tests were marked `slow`; PR #1580 cut it to 22.87 s (2,066 passed, 9 skipped). A one-test collection with `-n 16` alone took 12.63 s, so the 10 s target requires changing collection/worker overhead as well as test markers. Ticket 1700 remains open.
