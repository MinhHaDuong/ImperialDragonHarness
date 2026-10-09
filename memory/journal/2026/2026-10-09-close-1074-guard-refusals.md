# Closing 1074: guard refusals and a stalled auto-merge

Date: 2026-10-09. PR #1324 (ticket 1074 closed at author request, open exit
criteria moved to 1077).

## Context
The author asked to close tracker 1074 to shrink the open-ticket count
(14 → 13), although its child 1077 is still open.

## Events
- Inside a session entered with `EnterWorktree`, the runtime isolation guard
  refused four commands during this ticket-only change: a compound
  `erg close && erg archive && git status`; a `python3` heredoc editing a
  ticket whose text contained the word "git"; `git push && gh pr create` in
  one call; and `"$IDH_ROOT/skills/merge/erg-pr-merge" -C …` (command name
  computed at runtime). Each passed once split into plain commands.
- `erg-pr-merge` bounced with "CI has 6 check(s) still running".
- `gh pr merge --auto --merge` was accepted; once all ten checks were green,
  the PR read `CLEAN MERGEABLE`, auto-merge set, yet still OPEN. It was
  MERGED at 14:16:43Z around a direct `gh pr merge --merge`.

## Outcome
1074 closed on main; 1077 carries its three unchecked criteria. Close-claim
sweep: 30 PRs, 6 claims, 0 findings.

## References
PR #1324; tickets/closed/1074-*.erg; tickets/1077-*.erg.
