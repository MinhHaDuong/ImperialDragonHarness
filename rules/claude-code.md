<!-- last-reviewed: 2026-09-24 -->
# Claude Code idiosyncrasies

True of this runtime only: adapters on other runtimes skip this file.

## Entering the session

Except for `/hunt N` (below) and manuscript prose
([prose/workpackages.md](./prose/workpackages.md)), create the conversation's
worktree before answering with the plain-git recipe of `skills/hunt/SKILL.md` § Worktree
(`git worktree add`, `git worktree lock`, `cd`), named from the table below.
The `cd` moves the session; a restart resets it, so paths stay absolute.

Never call `EnterWorktree`. It switches on a runtime guard that refuses git
aimed at any other worktree, `-C` and `cd` alike, and the session's subagents
inherit it: review seats cannot reach their review tree.

| Context | Worktree name | Phase |
|---------|---------------|-------|
| Fresh conversation, no ticket | `explore-{topic}` | `[→ Imagine]` |
| Ticket reference but no branch | `t{N}-{pid}` | `[→ Plan]` |
| `/hunt N` | *decided inside hunt* | `[→ Plan]` |
| Active feature branch + open MR | `t{N}-{pid}` | `[→ Execute]` |
| MR review | `review-{N}` | `[→ Verify]` |

`{pid}` is `$PPID-$RANDOM`, as in hunt's § Worktree: subagents share `$PPID`.
Legacy bare `t{N}` names remain valid.

**`/hunt N`: do not create a worktree before the skill runs** — its detached
agent creates its own, orphaning yours.

Open with the phase label heading one self-presentation line, in the
conversation's language, then answer:

`[→ Execute] · <model> · effort <level, when the runtime states it> · MOE N+2 — government by intention via team leads; I filter, verify, surface, advise.`

## Subagent levers

- **Pin `model` on every launch** with the short token (`sonnet|opus|haiku|fable`).
  Agent definitions carry no `model:`: an unpinned `Agent` child or
  `Workflow` `agent()` inherits the session model. Choose per
  `skills/route/SKILL.md` and state why; a skill that launches workers must say
  so (`tests/test_launch_model_choice.py`). Independence is a family question
  (`skills/route/references/decorrelation.md`).
- **Effort is set per agent *definition*, not per `Agent` call**: `effort:` in
  a subagent's frontmatter pins it; `Workflow`'s `agent()` takes `opts.effort`,
  the only per-call lever. Unreliable on models with a pinned effort.
- **`team-lead` delegation needs a nesting depth of at least 2**, or it
  silently degrades into a flat agent; check it before debugging.
<!-- harness-extension-point -->
  Knobs: `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (3 in `settings.shared.json`), `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`.

## Allow rules

The classifier refuses rule-mandated force-pushes and `git branch -D` despite
the blanket `Bash` allow: `scripts/claude-allow-check.py` lists the narrow rules.

## Hook output

Hook stdout enters the conversation: **frame it declaratively**
("Worktree isolation is enabled…"), never as an imperative, which the model
discounts as prompt injection; the channel fails while looking fine.
