---
name: feedback_subagent_model_effort_levers
description: How model and effort actually propagate to spawned subagents — model needs a per-invocation pin, effort is set on the agent definition
metadata:
  type: feedback
---

Model and effort propagate to subagents differently, and neither propagates from skill frontmatter:

- **model**: a skill's `model:` frontmatter never reaches agents it spawns. Both the `Agent` tool and `Workflow`'s `agent()` default to the *session* model when no per-call `model` is passed. The only reliable rightsizing lever is a per-invocation `model` on each launch (short enum token `sonnet|opus|haiku` — a full `claude-*` id is only valid in frontmatter).
- **effort**: the plain `Agent` tool has no `effort` parameter, but that does not mean the child is stuck at session effort. `effort:` on the **agent definition** (a subagent's frontmatter, or the `--agents` JSON) pins that child; only a definition without the field inherits the session's. So the lever is per agent *type*, not per call, and moving session effort is not required. `Workflow`'s `agent()` additionally accepts `opts.effort` (`low|medium|high|xhigh|max`) per call, which remains the only genuinely per-call lever.

**Why:** the spawn mechanisms differ in their schema, not just convention — `Agent` genuinely has no `effort` field, `Workflow.agent()` genuinely does. Treating them as the same risks leaving `Workflow` fan-outs stuck at session effort when a cheap mechanical stage should run at `low` or a hard verify/judge stage at `high`+.

**How to apply:** when pinning model/effort for a fan-out, check which mechanism is spawning the child. Agent tool: model per-call, effort via session only. Workflow `agent()`: both model and effort are settable per-call — prefer low effort for cheap mechanical stages, reserve high/xhigh/max for hard verify/judge stages.

**Measured 2026-09-10**, Claude Code 2.1.267, model Opus 5, session effort `high`.
Each child records its own effort in
`~/.claude/projects/<proj>/<session-id>/subagents/agent-<id>.jsonl` (top-level
`"effort"` on each assistant record), with the sibling `.meta.json` naming the
`agentType` — that pair is the observation channel. Four runs:

| agent definition | child effort |
|---|---|
| no `effort` field | `high` (inherited) |
| `effort: low` | `low` |
| `effort: max` | `max` |
| `effort: bogus-level` | rejected at load: `probe.effort: Invalid input` |

The parent recorded `high` throughout. The no-field and `max` arms are the
controls that matter: without them, a single `low` reading is equally
consistent with "subagents always run low". Both the `--agents` JSON path and a
`.claude/agents/*.md` frontmatter file gave the same result, and 2.1.266
reproduced it, so on Opus 5 this lever predates the 2.1.267 changelog entry
("`effort:` frontmatter on custom commands, skills, and subagents being
ignored"). That entry scopes the bug to models whose default effort is pinned
(Opus 4.7, Opus 4.8, Fable 5), none of which were tested here: on those, treat
the frontmatter key as unreliable before 2.1.267.

The prior version of this note asserted the opposite for the `Agent` tool. It
generalised from the tool schema, where `effort` is genuinely absent, to the
child's behaviour, which the schema does not govern. A missing parameter proves
nothing about a value resolved elsewhere. See [[feedback_a_test_green_for_an_accidental_reason]].
