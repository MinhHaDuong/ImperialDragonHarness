# gaze — cases
Updated: 2026-11-10 · sources are observed review episodes, not new policy

## Other-family seat failed to start, PR 2399 — 2026-11-10
Context: receipts for the Zotero staging check. What happened: the codex seat failed ("cannot prepare the seat: No such file or directory") and the run reported REVIEWED on a self seat alone. Reaction: the raid re-ran gaze for the other-family read. Outcome: that seat found a file-name-only receipt match that would attach a replaced file to the old work, reproduced red before the fix. Source: memory/journal/2026/2026-11-10-raid-f7aac3-staging-recognition-and-receipts.md.
Use: a REVIEWED with a planned seat missing is not the planned review; rerun before gating.

## Seat cited the wrong tree, PR 2423 — 2026-11-10
Context: a Codex seat launched with `-m gpt-6-luna` reported `gpt-6.1-sol`. What happened: its one finding cited a line of the lead's session worktree (old main), not the PR head, where the check is conditional and tested. Reaction: not adopted; the gate weighed and upheld the rejection. Source: memory/journal/2026/2026-11-10-roar-raid-45e130-fleet-audit-trace-runtimes.md.
Use: check a seat's finding against the reviewed head before adopting it, and record the model the seat reports.

## Cleanup's apparent safe copy, PR 2216 — 2026-11-05
Context: cleanup treated setup copies and primary links as expendable. What happened: first gaze reproduced a primary counterpart pointing back to the only copy in the tree being removed. Reaction: the fix rejected counterparts resolving inside that tree. Outcome: second gaze confirmed. Source: memory/journal/2026/2026-11-05-t1406-worktree-copy-review.md.
Use: a counterpart's apparent primary location did not prove that removing the candidate preserved a copy.

## Neighboring leak after each scrub fix, PR 2054 — 2026-10-30
Context: seat-output scrubbing underwent six gaze rounds. What happened: each fix exposed a neighboring leak; the author authorized extensions after rounds 3 and 5. Reaction: round 6 found another blocker; the PR was parked and redesign ticket 1378 filed. Source: memory/journal/2026/2026-10-30-raid-80974c.md.
Use: repeated neighboring failures were evidence about the approach; those author extensions were scoped to this PR.
