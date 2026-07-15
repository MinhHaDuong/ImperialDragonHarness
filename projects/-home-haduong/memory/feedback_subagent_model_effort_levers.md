---
name: feedback_subagent_model_effort_levers
description: How model and effort actually propagate to spawned subagents — model needs a per-invocation pin everywhere, effort only via Workflow's agent()
metadata:
  type: feedback
---

Model and effort propagate to subagents differently, and neither propagates from skill frontmatter:

- **model**: a skill's `model:` frontmatter never reaches agents it spawns. Both the `Agent` tool and `Workflow`'s `agent()` default to the *session* model when no per-call `model` is passed. The only reliable rightsizing lever is a per-invocation `model` on each launch (short enum token `sonnet|opus|haiku` — a full `claude-*` id is only valid in frontmatter).
- **effort**: the plain `Agent` tool has no `effort` parameter at all — a spawned child always inherits the session's reasoning effort, so the only lever is setting the session effort before the fan-out. `Workflow`'s `agent()` is different: it accepts `opts.effort` (`low|medium|high|xhigh|max`) directly per call, independent of session effort.

**Why:** a prior version of `rules/workflow.md` overstated this as "effort is not a launch parameter" without qualification, which was wrong for `Workflow.agent()` and risked underuse of per-call effort tuning in workflow scripts (corrected 2026-07-15 — caught by the user noticing the harness text was overbroad, no ticket).

**How to apply:** when pinning model/effort for a fan-out, check which mechanism is spawning the child. Agent tool: model per-call, effort via session only. Workflow `agent()`: both model and effort are settable per-call — prefer low effort for cheap mechanical stages, reserve high/xhigh/max for hard verify/judge stages.
