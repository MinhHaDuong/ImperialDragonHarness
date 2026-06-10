---
name: feedback_subagent_model_effort_levers
description: How model/effort actually resolve for spawned subagents — skill frontmatter does NOT propagate; per-invocation model is the only reliable lever; effort is not an Agent launch param at all
metadata:
  type: feedback
---

Rightsizing a fan-out skill: the **per-invocation `model`** on each Agent/Workflow
launch is the only reliable lever. The traps (PR #360 / ticket 0235, 2026-06-10):

- **Skill `model:` frontmatter is NOT in the subagent inheritance chain.** A child
  spawned via the **Agent tool** resolves model as: `CLAUDE_CODE_SUBAGENT_MODEL`
  env > per-invocation `model` param > subagent-definition frontmatter > **session
  model**. The invoking skill's frontmatter never enters this chain, so an unpinned
  launch silently runs at the *session* model. `raid` pinned only decorative
  frontmatter (`claude-opus-4-6`/`max`) and left every fan-out agent unpinned →
  whatever the session ran.
- **Workflow `agent()` inherits the session model** (not the skill's), and its
  `opts` are `{label, phase, schema, model, isolation, agentType}` — pin `model`
  there too.
- **`effort` is NOT an Agent launch parameter** (the Agent tool schema has no
  `effort`) and is NOT a Workflow `agent()` opt. A spawned child runs at the
  *session* effort — you cannot pin a child's effort per-call. Frontmatter
  `effort:` only overrides effort *while that skill's own inline context is
  active* (documented); it does not reach spawned children.
- **Per-invocation `model` token enum is `sonnet|opus|haiku|fable`** — short forms.
  The full id (`claude-fable-5`) is valid only in frontmatter (different code
  path); passing it as the Agent `model` param is an InputValidationError.
- **`CLAUDE_CODE_SUBAGENT_MODEL`** is precedence #1 — a global cap that overrides
  even deliberate per-invocation pins, so don't set it blindly (it would clobber
  maw-audit/test-audit-llm's Opus/Sonnet tiering). Unset by default.

**Why:** the harness's stated rule (`rules/workflow.md:79`, "reviewers below the
coder tier") was real in only ~3 of ~30 skills; everything else inherited the
session model, so a top-tier session fanned out top-tier agents. **How to apply:**
when a skill spawns agents, pin `model` per-launch (reviewers→`sonnet`, mechanical
lookups→`haiku`, coders→`fable`, cross-tier skeptics deliberately one tier up);
set session effort before running a fan-out skill; never trust frontmatter
`model:`/`effort:` to govern children. See [[feedback_workflow_agents_session_bound]],
[[feedback_harness_is_the_deliverable]].
