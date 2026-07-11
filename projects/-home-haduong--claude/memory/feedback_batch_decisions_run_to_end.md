---
name: batch-decisions-run-to-end
description: Author doctrine — frontload all interactive questions in one batched round, then run autonomously through verify/merge/cleanup to a single final report; never make the author watch a spinner
metadata:
  type: feedback
---

Author doctrine (2026-07-11, stated twice in one session and promoted to
rules/workflow.md § Autonomous Action Rules "Batch the decisions, then run to
the end"): with long-run-capable agents, the preferred interaction mode is to
collect as much feasible work as possible up front — one dense
question round with recommended defaults — then work autonomously to
completion. Watching a spinner is not a good use of the author's time.

**Why:** the author's attention is the scarcest resource; sequential
questions and progress check-ins each burn a context switch, while the
autonomous tail (gaze, merges, cleanup) needs none of them.

**How to apply:** before starting a multi-step task with known decision
points, enumerate them and ask ALL of them in one AskUserQuestion round (up
to 4 questions); delegate waits to background agents instead of holding the
conversation; return mid-run only for genuinely new scope or irreversible
actions the batch did not cover; end with one consolidated report. The rule
text is authoritative; this entry records the origin.
