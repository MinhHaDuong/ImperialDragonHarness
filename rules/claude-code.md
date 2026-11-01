<!-- last-reviewed: 2026-09-24 -->
# Claude Code idiosyncrasies

True of this runtime only: adapters on other runtimes skip this file.

## Entering the session

Worktree, naming and opening line: `workflow.md` § Session start, details in `skills/hunt/references/session-start.md`. The `cd`
moves the session; a restart resets it, so paths stay absolute.

Never call `EnterWorktree`. It switches on a runtime guard that refuses git
aimed at any other worktree, `-C` and `cd` alike, and the session's subagents
inherit it: review seats cannot reach their review tree.

## Subagent levers

- **Pin `model` on every launch** with the short token (`sonnet|opus|haiku|fable`).
  Agent definitions carry no `model:`: an unpinned `Agent` child or
  `Workflow` `agent()` inherits the session model. Choose per
  `skills/route/SKILL.md` and state why; a skill that launches workers must say
  so (`tests/test_launch_model_choice.py`).
- **Effort is set per agent *definition*, not per `Agent` call**: `effort:` in
  a subagent's frontmatter pins it; `Workflow`'s `agent()` takes `opts.effort`,
  the only per-call lever. Unreliable on models with a pinned effort.
- **`team-lead` delegation needs a nesting depth of at least 2**, or it
  silently degrades into a flat agent; check it before debugging.
<!-- harness-extension-point -->
  Knobs: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (3 in `settings.shared.json`), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`.

## Allow rules

The classifier refuses skill-prescribed force-pushes and `git branch -D` despite
the blanket `Bash` allow: `scripts/claude-allow-check.py` lists the narrow rules.
A classifier denial is rewritten to match an allow rule literally (`git -C`,
no `cd` prefix) or logged and skipped, never retried verbatim.

## Hook output

Hook stdout enters the conversation: **frame it declaratively**
("Worktree isolation is enabled…"), never as an imperative, which the model
discounts as prompt injection; the channel fails while looking fine.
