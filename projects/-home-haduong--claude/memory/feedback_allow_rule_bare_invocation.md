---
name: allow-rule-bare-invocation
description: settings.json allow rules prefix-match the WHOLE command text — a compound (cd X && cmd) never matches and falls to the stochastic classifier; invoke the rule-covered command bare, exactly as spelled in the rule
metadata:
  type: feedback
---

2026-07-14 wave #601-#603: three gaze-APPROVED, CI-green PRs sat parked
because every `cd <worktree> && … && erg-pr-merge N` invocation was denied by
the auto-mode classifier — while the standing rule
`Bash(~/.claude/skills/merge/erg-pr-merge:*)` (committed 2026-07-10) had
authorized the merge all along. Allow rules are deterministic and evaluated
BEFORE the classifier, but they prefix-match the literal command text: any
prepended `cd`, `env`, variable assignment, or absolute-path respelling of a
`~`-spelled rule misses the match and drops to the classifier lottery.

**Why:** the classifier is per-call stochastic (identical compounds passed
for #601 and were denied for #602); a settings rule is the only durable,
deterministic authorization. Fighting the classifier with rephrasing is
wasted rounds — check `permissions.allow` FIRST and shape the command to
match an existing rule exactly.

**How to apply:** before escalating a permission denial to the user, read
`settings.json` `permissions.allow` for a rule covering the capability, then
invoke the command bare, spelled exactly as the rule spells it (keep `~` if
the rule uses `~`). For cwd-dependent scripts run bare, either the script
takes a path flag ([[0344|erg-pr-merge -C]]) or put the required branch under
the checkout that the session cwd resolves to (primary-checkout dance:
`git -C <primary> worktree remove <pr-worktree>` then `git -C <primary>
checkout <branch>`; back up + reapply any dirty files around it). Side
effect of a cwd outside any checkout: erg-pr-merge finds no `tickets/erg`
and silently SKIPS the ticket close — follow with the chore-close recipe.
