<!-- last-reviewed: 2026-09-09 -->
# Claude Code idiosyncrasies

Everything here is true of the current runtime and of nothing else. It is split
out so an adapter on another runtime (Pi, Codex — tickets 0800, 0802) can load
the rest of `rules/` and skip this file. Capabilities belong in the other rule
files; the tool names that provide them belong here.

## Entering the session

The SessionStart hook prints the worktree instruction and the effort setting.
Call `EnterWorktree` before answering, then `git switch <branch>`.

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

**Carve-out for `/hunt N`: do not enter a worktree before the skill runs.**
Hunt triages the ticket first (`skills/hunt/SKILL.md` is the authority): a
pre-emptive `t{N}-*` worktree makes its ownership check read the interactive
session as an already-detached executor, and the triage is skipped.

Open with the phase label heading one self-presentation line, in the
conversation's language, then answer:

`[→ Execute] · Fable 5 · effort high · MOE N+2 — government by intention via team leads; I filter, verify, surface, advise.`

## Subagent levers

- **Pin `model` on every fan-out launch — frontmatter does not propagate.** A
  skill's `model:` never reaches the agents it spawns: an `Agent` child resolves
  to the session model, a `Workflow` `agent()` inherits it. Set it per launch,
  with the short enum token (`sonnet|opus|haiku|fable`); a full `claude-*` id is
  valid only in frontmatter. Reviewers below the coder tier, mechanical lookups
  at `haiku`, coders at the top tier. Enforced by
  `tests/test_model_rightsizing.py`.
- **Effort is not settable on the `Agent` tool.** A spawned child inherits the
  *session* effort, so pin it by setting session effort before the fan-out.
  `Workflow`'s `agent()` takes `opts.effort` (`low|medium|high|xhigh|max`) per
  call. Mechanics: memory `feedback_subagent_model_effort_levers`.
- **`team-lead` delegation needs a nesting depth of at least 2.** A team lead
  mobilizes its own executors, so a runtime that forbids nested spawning
  silently degrades every delegation into a flat agent doing the work itself —
  the delegation still returns, just without a team. This default has flipped
  twice in three releases: when delegations come back suspiciously flat, check
  the platform default before debugging the prompt.
<!-- harness-extension-point -->
- *Current-generation knobs, names that rot:* `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20)
  <!-- harness-extension-point --> and `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (default 3).
  The two capabilities above do not rot; these spellings will.
- **A fork resumed via `SendMessage` can mistake itself for the coordinator.** A
  fork inherits the parent's history including the parent's own act of
  dispatching it, so a resume framed as "you are a subagent reporting to a
  coordinator" can read, from its inherited view, as an external claim
  contradicting what it watched itself do. Two forks denied having finished real
  work and treated the re-grounding as prompt injection (ticket 0551). One
  resume attempt is worth trying; if it drifts again, read what it produced in
  the shared worktree, or redo the work in the parent session.

## Hook output

Hook stdout enters the conversation as context, so **frame it declaratively**
("Worktree isolation is enabled…"), never as an imperative instruction
("INSTRUCTION: call EnterWorktree now"). The model classifies imperative hook
text as prompt injection and discounts it — the channel then fails while looking
like it worked.
