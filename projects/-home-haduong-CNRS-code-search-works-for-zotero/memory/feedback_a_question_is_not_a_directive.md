---
name: a-question-is-not-a-directive
description: "The author's probing question about a plan tests the reasoning; it is not an order to reshape the work — confirm before redirecting a running agent"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6c21d767-95a0-4e11-8ec4-b9730449bfdb
  modified: 2026-09-03T11:38:12.166Z
---

The author asked "So the implementation plan is to add the columns one by one as
variables, until we say basta this is actually a registry?" I read it as a
verdict against incrementalism, reshaped the upstream contribution from a focused
pooling fix into an explicit-registry PR, and redirected the running build agent.
His next message: "Not sure about the revised plan. I thought adapting to the
maintainer and shipping just the pooling fix was smart."

**Why:** He probes to test whether the reasoning holds, and a question phrased as
a sharp characterization is still a question. Acting on it cost a redirect, a
revert, and a build agent that received three conflicting briefs in one session —
the confusion risk that [[feedback_executor_gate_loop_stall]] and the fork-drift
lesson both warn about.

**How to apply:** When a question implies a different plan, answer the question
and state which way it points, but do not change delivered or in-flight work
until he says so. One sentence — "that reads as a critique of X; want me to
reshape, or was that a check on the reasoning?" — costs a turn and saves a
reversal. Distinguish his imperatives ("I want a rebuild", "file it") from his
interrogatives; the first are orders and [[feedback_execute_authorized_outward_actions]]
applies, the second are not.

**The substance he was right about**, worth keeping separately: adapting to the
maintainer's chosen design beats arguing with it. Design-shaped contributions to
zoteus come back as the maintainer's own implementation, five for five; focused
defect fixes merge, twelve for twelve with none closed unmerged (counted on the
forge 2026-09-03). A curated per-model table shipped as a bug fix plants the
registry's first column and lets him reach the conclusion himself, the way he
reached "dtype must be in the identity" on his own.
