<!-- last-reviewed: 2026-09-24 -->
# Claude Code idiosyncrasies

True of the current runtime only: an adapter on another runtime (Pi, Codex)
loads the rest of `rules/` and skips this file.

## Entering the session

Except for `/hunt N` (below) and manuscript prose
([prose/workpackages.md](./prose/workpackages.md)), call `EnterWorktree` before answering, then `git switch <branch>`.

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

- **Pin `model` on every launch** with the short token (`sonnet|opus|haiku|fable`).
  Frontmatter never reaches spawned children: an unpinned `Agent` child or
  `Workflow` `agent()` inherits the session model. Choose the worker per
  `skills/route/SKILL.md` and state why; a skill that launches workers must say
  so (`tests/test_launch_model_choice.py`). Independence is a family question
  (`skills/route/references/decorrelation.md`).
- **Effort is set per agent *definition*, not per `Agent` call**: `effort:` in
  a subagent's frontmatter pins it; `Workflow`'s `agent()` takes `opts.effort`,
  the only per-call lever. Unreliable on models with a pinned default effort.
- **`team-lead` delegation needs a nesting depth of at least 2**, or it
  silently degrades into a flat agent; check it before debugging the prompt.
<!-- harness-extension-point -->
  Knobs: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`.

## Hook output

Hook stdout enters the conversation as context: **frame it declaratively**
("Worktree isolation is enabled…"), never as an imperative, which the model
discounts as prompt injection — the channel then fails while looking fine.
