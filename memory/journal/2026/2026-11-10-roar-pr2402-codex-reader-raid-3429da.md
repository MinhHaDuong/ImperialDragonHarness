# Roar, PR 2402: the context audit reads Codex sessions (ticket 1508, raid 3429da)

Date: 2026-11-10. Host: padme. Tracker: ticket 1507; sibling: ticket 1509 (Pi).

## Context

The author asked for `/raid 1507 the codex part`, then, minutes into the run,
for a second agent to raid the Pi part, coordinated. Ticket 1507 covered both
runtimes with one set of exit criteria.

## What happened

- Ticket 1507 became a tracker with two children, filed and merged as a
  ticket-only request before any other work (PR 2398): 1508 owns everything
  the two runtimes share (the reader seam, the runtimes-read report,
  could-not-look, the exit code) plus the Codex reader; 1509 adds the Pi
  reader and was `Blocked-by: 1508`.
- The Pi raid (raid 626455, a team lead launched as a subagent) ran Select,
  Imagine, Plan and feasibility while the Codex executor worked, and held
  Execute until 1508 merged. Its first report listed what the Pi reader
  needed from the seam; all of it was in the seam the Codex executor pushed,
  read from the pushed head before the gate. No message was sent to the
  running executor.
- Imagine, Plan and feasibility for 1508 were written by the raid lead in one
  annotation commit (PR 2400); only the Blind-Spot pass ran as a separate
  seat. It returned four findings in 84 s: the Codex archive directory and
  `CODEX_HOME`, the role split of the ten-day corpus (265 `exec`, 222
  subagent, 25 `cli` of 512), conversation order in the seam, and the host
  the audit reads.
- A shape probe of 120 recent rollouts, run before the split (key names and
  numbers only), gave `cached_input_tokens <= input_tokens` on 2771 of 2771
  `token_count` records. The executor's run over 28 days gave
  `total == input + output` on all 64993 records with a cached part.
- PR 2397, another session's interim line in the same script, was open and
  gate-APPROVED when the executor forked. Its owner said it was parked and to
  fork without it; PR 2402's body said it superseded 2397. The author then
  landed 2397 ("land 2397") at 08:41:04Z, ten seconds after verify-gate wrote
  its record for PR 2402. The gate refused to rule: its verdict write was
  rejected as stale, no round was spent, and it posted one comment.
- Recovery took 14 minutes from the refusal to the merge: the executor,
  resumed with its context, merged main into the branch (no force-push) and
  removed 2397's 13 lines in 96 s; a narrow gaze on the merge commit returned
  REVIEWED in 3m31s, with a mutation control showing which assertions pinned
  the resolution; the gate returned APPROVED, round 1, in 2m46s.
- `raid_land.py 2402` ran from the raid lead's session without a permission
  refusal, after gaze and gate in the same session.

## Outcome

PR 2402 merged at head 81e09639 (main 2c1b4608). On padme since 2026-11-01
the audit counted 235 Codex main sessions (214 `exec`, 21 `cli`) beside 287
Claude Code ones, 4 Codex sessions with 30 or more turns at or above 230K,
none past its ceiling. The Pi raid received its go on that main.

## Decisions already made

- Codex `exec` sessions are held to the default ceiling, `cli` to their
  model's (ticket 1508, plan point 2).
- Queued for the author: whether the count means this host or the fleet; and
  the Pi raid's default of reading the Pi seat spool at the default ceiling.

## References

PRs 2398, 2400, 2401, 2402, 2397. Review `rv-20261110-pr-2402-d183`. Gate
session `9b3c856a-c8f4-4c64-a6b4-9a1a1a8145be`. Raid log, raid `3429da`.
Sweep: `scripts/trace-stats.py`, `scripts/trace-friction.py` and
`scripts/trace-wall-time.py` also read the Claude Code corpus only.
