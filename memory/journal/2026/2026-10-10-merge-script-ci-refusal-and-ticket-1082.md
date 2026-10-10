# Merge script refused on pending CI; ticket 1082 (2026-10-10)

Continues [permissions allow-all and idh install sync](2026-10-10-permissions-allow-all-and-idh-install-sync.md). PRs #1345, #1347, #1349.

## Observed
- `erg-pr-merge` exited at `skills/merge/erg-pr-merge:148` with "CI has 10 check(s) still running" on #1345, seconds after the PR opened. The caller ended its turn and the PR stayed open about an hour; all 10 checks had passed within about two minutes (slowest `pytest-guard`, 1m36s). The script's step 3 states that `--auto` lets the forge gate on required checks.
- The author listed three options (track CI duration; one command returning failed-or-merged; local CI only). Ticket 1082 was filed for the first two plus an arm-auto-merge-immediately variant (#1347); ticket 1045 already covers the local-CI option.
- The first draft priced option 2 as `gh pr checks --watch` in the background. The author asked that it not be a bash sleep loop, noting these hang, and that portability be considered. #1349 rewrote it as a one-shot status command (exit 0 merged, 1 failed, 2 pending) with portability constraints, citing ticket 0889 (105 agent-written waiters in 551 sessions).
- Later PRs (#1347, #1349) were merged with `gh pr merge --auto --merge` directly, not through `erg-pr-merge`; #1349 showed "no checks" on one read and all 10 passing on the next.
- A commit message for the budget fix first stated, untested, that a shortened index line would still be over budget; it was amended before the push.

## Disclosed gaps
- Nothing in tickets 1081 or 1082 is implemented; the rates they ask for are unmeasured.
- `erg-pr-merge` lines ~380-460 (the watch-then-merge fallback) were not read.
