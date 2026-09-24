<!-- last-reviewed: 2026-09-24 -->
# Claude Code idiosyncrasies

True of the current runtime only: an adapter on another runtime (Pi, Codex)
loads the rest of `rules/` and skips this file.

## Entering the session

Except for `/hunt N` (below) and manuscript prose (`git.md` § Prose
workpackages), call `EnterWorktree` before answering, then `git switch <branch>`.

| Context | Worktree name | Phase |
|---------|---------------|-------|
| Fresh conversation, no ticket | `explore-{topic}` | `[→ Imagine]` |
| Ticket reference but no branch | `t{N}-{pid}` | `[→ Plan]` |
| `/hunt N` | *decided inside hunt* | `[→ Execute]` |
| Active feature branch + open MR | `t{N}-{pid}` | `[→ Execute]` |
| MR review | `review-{N}` | `[→ Verify]` |

`{pid}` is a short session discriminator so two sessions on one ticket land in
distinct paths; resolve `$$` with `bash -c 'echo $$'` first, since the name
schema rejects `$`. Legacy bare `t{N}` names remain valid.

**`/hunt N`: do not enter a worktree before the skill runs** — a pre-emptive
`t{N}-*` worktree makes its ownership check skip the triage.

Open with the phase label heading one self-presentation line, in the
conversation's language, then answer:

`[→ Execute] · Fable 5 · effort high · MOE N+2 — government by intention via team leads; I filter, verify, surface, advise.`

## Subagent levers

- **Pin `model` on every fan-out launch — frontmatter does not propagate.** A
  skill's `model:` never reaches the agents it spawns: an `Agent` child resolves
  to the session model, a `Workflow` `agent()` inherits it. Set it per launch,
  with the short enum token (`sonnet|opus|haiku|fable`); a full `claude-*` id is
  valid only in frontmatter. A `context: fork` skill is the exception for its
  own fork: frontmatter `model:` pins it (probe, 2026-09-23), and unpinned it
  inherits the caller's tier, so pin every forked skill. Reviewers below the
  coder tier, mechanical lookups at `haiku`, coders at the top tier. Enforced
  by `tests/test_model_rightsizing.py`.
- **Effort is set per agent *definition*, not per `Agent` call**: `effort:` in
  a subagent's frontmatter pins it; `Workflow`'s `agent()` takes `opts.effort`,
  the only per-call lever. Unreliable on models with a pinned default effort
  (memory `feedback_subagent_model_effort_levers`).
- **`team-lead` delegation needs a nesting depth of at least 2**, or it
  silently degrades into a flat agent. The default has flipped twice: when
  delegations come back flat, check it before debugging the prompt.
<!-- harness-extension-point -->
- *Current-generation knobs, names that rot:* `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20)
  <!-- harness-extension-point --> and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3).
  The two capabilities above do not rot; these spellings will.
- **A fork resumed via `SendMessage` can mistake itself for the coordinator**
  (it inherited the dispatch) and reject re-grounding as injection. Try one
  resume; if it drifts, read its output in the shared worktree or redo the work.

## Hook output

Hook stdout enters the conversation as context: **frame it declaratively**
("Worktree isolation is enabled…"), never as an imperative, which the model
discounts as prompt injection — the channel then fails while looking fine.
