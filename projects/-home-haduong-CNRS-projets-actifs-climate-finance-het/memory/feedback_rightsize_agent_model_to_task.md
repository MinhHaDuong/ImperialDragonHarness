---
name: feedback_rightsize_agent_model_to_task
description: "Pin subagent model to task difficulty, not habit — Fable is an available tier"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9f31f8d8-960b-4845-90b4-5e3056ada759
---

Rightsize the `model` parameter on every Agent/Workflow dispatch to the actual
difficulty of the task, don't default to the top tier. Fable (`fable`) is an
available model choice alongside `sonnet`/`opus`/`haiku`.

**Why:** caught 2026-07-17 mid-R&R-session — dispatched a factual web-research
lookup (IBRD cost of capital, sourced figures from public documents) at
`model: opus`. The task was multi-source fact-gathering with citation
discipline, not a task requiring the top reasoning tier; a cheaper/faster
model would have done it as well. Author flagged it live.

**How to apply:** before setting `model` on a dispatch, ask what the task
actually demands — mechanical lookups and factual research fit `haiku`/`fable`;
synthesis, judgment calls, and adversarial verification warrant `sonnet`;
reserve `opus` for the hardest reasoning/verification passes. See also the
harness rule in `~/.claude/rules/workflow.md` § Subagents on pinning `model`
per-invocation (that rule covers *that* frontmatter doesn't propagate — this
memory covers *which tier* to pick).
