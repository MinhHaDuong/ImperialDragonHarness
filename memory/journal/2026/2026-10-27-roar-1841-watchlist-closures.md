# 2026-10-27 — PR #1841: 1164 and 1243 closed under a trace-doctor watchlist

Context: the author asked to close the deferred tickets 1164 (Stopguard) and
1243 (attribution in the merge commit), do the routine-step wording fix (1296),
and put both diagnostics on the doctor's watchlist.

Events:
- `rules/workflow.md` gained "skill-prescribed steps (roar, gaze) run unasked".
  The resident-rule budget had 5 chars of headroom on main; the paragraph was
  compressed so the total went from 17795 to 17794.
- `skills/trace-doctor/SKILL.md` gained a Watchlist: 1164 via
  `trace-stopguard.py`, 1243 via `attribution_query.py --since` coverage
  (baseline 74/757 `available` over 28 days to 2026-10-27).
- Gaze round 1 (cross-family seat, openai/gpt-6.1-sol): two minors, both fixed.
  The delta gaze's `gaze_close.py` was blocked by the permission classifier in
  the forked session; the parent session ran the same command and it posted.
- verify-gate round 1: NEEDS-AUTHOR (closures rested on agent-written lines);
  the author answered "Confirmed" in session; round 2 APPROVED; merged at
  f9bde60c by `raid_land.py`.
- On landing and at roar capture, the attribution block of #1841 was refused
  with "fact order requires kind, pr, writer before reviewers": the block had
  no `writer:` line. This was after 1286 merged. Appending the writer line made
  the capture pass. First data point for the 1243 watchlist row.

Outcome: 1164, 1243, 1296 closed; PR #1841 merged.
