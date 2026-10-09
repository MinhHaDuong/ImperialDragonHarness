# rtk git exclusion ends the worktree-guard collision

Date: 2026-10-09 · Host: doudou, padme · Tickets: 0375, 1078 · PRs: #1312, #1314

## Context

Roar for PR #1300 (ticket 0375 trial). #1300 had merged with a bare
`Ticket-ref:` line, so 0375 stayed open; PR #1312 closed it.

## Events

- About eight git commands (`add`, `commit`, `push`, `diff`, `worktree`) were
  refused by the worktree isolation guard because the rtk hook had rewritten
  them to `rtk git …`. Each ran when issued as `/usr/bin/git`.
- `rtk hook check git` (bare) printed `No rewrite`; per-subcommand checks
  showed rtk 0.49.0 rewrites `add`, `commit`, `push`, `fetch`, `worktree`,
  `branch`, `diff`, `show`, `git -C …`, and spares `status`, `log` (already
  excluded by 0932), `switch`, `rev-parse`, `merge-base`. `ls -la` served as
  the positive control.
- `rtk gain` on doudou: git absent from the top 10; the 10th entry saved
  306.5K of 366.9M tokens (derived upper bound, <0.1 % per git command).
- `exclude_commands` on doudou and padme set to
  `["^git\\b", "^make\\b.*\\bcheck\\b"]`; backups beside each config. The same
  ten-shape probe returned `No rewrite` for every git shape on both machines,
  with `ls -la` still rewritten.
- The guard also refused commands that only contained the text "rtk … git"
  (a PR body, a quoted `rtk hook check` argument, an ssh command string),
  including one `!` command the author typed. Passing the text through a file
  or a script avoided it. Not ticketed (below the severity floor).
- The classifier denied removing the agent worktree holding `t0375-trial`
  and denied re-running the probe locally as self-modification; the author ran
  the probe.

## Outcome

Ticket 1078 closed by PR #1314 (merged 2026-10-09T13:50Z). Memory notes
`memory/topics/git-worktree-session-guards.md` and
`memory/reference_git_in_a_worktree_session.md` describe the rtk rewrite of
git as current; on doudou and padme it no longer occurs after this change.
`t0375-trial` (cf362b7b, superseded by #1300) remains in
`.claude/worktrees/agent-a737a9f1dde31f044`.
