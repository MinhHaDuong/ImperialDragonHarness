# Raid 2026-10-28 on tracker 1298: F1 review evidence on local notes

Context: `/raid 1298`, one ticket named by ID. Imagine counted ~20 files around the `## /gaze result`
PR-comment contract; the Blind-Spot pass found a two-step split would leave gaze writing notes while
verify-gate and attribution read comments. 1298 became a tracker with children 1299, 1300, 1301
(PR #1851, ticket-only).

Events:
- 1299 (PR #1852, merged a792e2bd): `push_for_landing` before the merge. First gaze FINDINGS: the
  no-op path called `setup()`, writing exact `refs/notes/review` fetch refspecs; a plain
  `git fetch origin` then exited 128 against an origin without notes (3 `test_after_merge` tests red).
  Fixed; gate APPROVED round 1.
- 1300 (PR #1855, merged 8acd4553): notes evidence for PR units keyed `pr:<n>`, local writes with a
  detached background sync, stale-tolerant readers. First gaze FINDINGS (both seats, reproduced): two
  clones could each record a round-1 verdict and landing pushed both. Fixed by refusing split rounds at
  landing. Gaze item 3 (open a review offline on first discovery) kept fail-closed after an advisor
  call (Fable); decision logged on ticket 1300. Gate APPROVED round 1.
- 1301 (PR #1858, merged 6d749bcb): PR comment becomes a pointer, readers on notes, texts and STATE.
  First gaze FINDINGS: a `gh` timeout escaped `pointer()`. After the fix the gate refused admission
  twice (no round spent): the orchestrator's gaze intents were recorded as delta answers, once from a
  custom intent and once with `scope: full` written inside the intent line; a default-intent gaze was
  admitted. A full gaze returned ESCALATE once on a plan-check failure from
  `tests/test_attribution_backfill.py` failing to collect when run alone (also on main); fixed inline.
  Gate APPROVED round 1. Its landing was the first to push `refs/notes/review` and `pr:<n>`
  review-heads to origin before a merge.
- Attribution blocks of #1852 and #1855 needed hand repair after merge (duplicate reviewer line,
  reviewer lines without `seat=`/`status:`, `finding:` lines outside the parser's shape) before
  capture.

Outcome: tracker 1298 integration review PASS; `make check` on main 6d749bcb: 2829 passed, 4 skipped.
Residuals are logged on tickets/closed/1298.
