# A background service outlived the session's wrap-up (2026-10-06)

Context: the session recorded in `memory/journal/2026/2026-10-06-local-ci-act-equivalence.md`
(local CI with `act` under rootless podman). Its wrap-up ran `/roar` after the
last merge, then the worktree and the merged branches were removed.

## Observed

- During the work, a podman service was started by hand as a background task
  (`podman system service --time=0` on a dedicated socket, with a `keep-id`
  configuration), to try `act` against it. `--time=0` means it never exits on its
  own. The runner script that came out of the work starts its own service and
  stops it when it exits, including after an interruption; the hand-started one
  was not that service.
- After `/roar` had finished and the author asked "all set?", a check for leftover
  processes found the service still running, 12 h 42 min after it was started
  (started 2026-10-05 22:35 local time, with its parent shell). No container
  was running. It was stopped by process id; the socket file was gone afterwards.
- `/roar` has no step about processes: its text limits it to its own merged
  worktree and branches, and says it touches nothing outside them. `/lair` and
  `/molt` do not mention services started by a session either; `/molt` looks at
  live processes only to avoid removing a worktree one of them is working in.
  The service was found by the question, not by any of the three.

## Roles stated to the author

`/roar` after a merge, `/lair` at the end of the day, `/molt` for repository
housekeeping (git sync, health check, eager repairs, tickets for open findings).
A session can chain several merges, so a process started for the first may still
serve the third.

## Decision by the author

The author asked whether `/roar`'s instructions should change, and settled that
this is an experiential memory and not a change of instructions. No rule, skill
or script was modified for it.
