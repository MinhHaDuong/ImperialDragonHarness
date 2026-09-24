---
name: feedback_gate_proportionate_to_risk
description: "Size the merge gate to the PR's risk — full /gaze cost ~75 min and ~1M tokens on one data PR; a checklist review does it in ~15 min"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 36288e08-760c-498d-809d-4ea0d872d521
  modified: 2026-09-23T18:57:58.324Z
---

Size the merge gate to the risk, and never resume a fat executor for a small fix.

- Data-migration PR: one time-boxed (~15 min) checklist review agent in its own worktree — reproduce byte identity of served views, determinism (two builds), validator mutations rejected with named reasons, counts, exit criteria, check-fast + lint once — then merge. Measured 2026-09-23: 0873's checklist review took 11 min; full /gaze on 0872 took ~75 min, 9 agents, ~1M tokens, then idled retrying `reviewers scorecard` and never returned.
- Presentation or small follow-up PR: a proportionate check by the orchestrator (targeted grep/render probes, data/ diff scope), gate evidence posted as a PR comment.
- Small edits (a column width, a count fix): a fresh small agent or do it inline. Resuming the executor that carried seven batches (≈560k tokens of context) cost 25 min for one CSS change.

**Why:** the author called both out the same day ("25 min to fix a column width", "you will use gaze, the fat executor, in the same breath", "that gaze has been running for hours").

**How to apply:** state the gate tier in the plan before launching; relates to [[feedback_agent_briefs_scoped_gates]] and [[feedback_helper_agent_needs_own_worktree]].
