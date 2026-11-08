# gaze — cases
Updated: 2026-11-08 · sources are observed review episodes, not new policy

## Cleanup's apparent safe copy, PR 2216 — 2026-11-05
Context: cleanup treated setup copies and primary links as expendable. What happened: first gaze reproduced a primary counterpart pointing back to the only copy in the tree being removed. Reaction: the fix rejected counterparts resolving inside that tree, with controls for direct and parent-directory links. Outcome: second gaze confirmed both, then the gate passed in a checkout with an independent Git common directory. Source: memory/journal/2026/2026-11-05-t1406-worktree-copy-review.md.
Use: a counterpart's apparent primary location did not prove that removing the candidate preserved a copy.

## Neighboring leak after each scrub fix, PR 2054 — 2026-10-30
Context: seat-output scrubbing underwent six gaze rounds. What happened: each fix exposed a neighboring leak; the author authorized an option after round 3 and one last round after round 5. Reaction: round 6 found another blocker; the PR was parked and redesign ticket 1378 filed. Outcome: the original approach did not land. Source: memory/journal/2026/2026-10-30-raid-80974c.md.
Use: repeated neighboring failures were evidence about the approach; those exceptional author extensions were scoped to this PR.

## Fixture interference and two attempts, PR 2257 — 2026-11-07
Context: the native code inspection was clear, but the controller's example test failed when another process updated shared gate notes. Reaction: the fixture moved to a disposable minimal repository; the standalone example stayed unchanged. Outcome: the same actual review context returned FINDINGS, then REVIEWED after the fix. Source: memory/journal/2026/2026-11-07-raid-d35fb4.md.
Use: preserve the controller catch and both attempts; neither a second independent reviewer nor a native-seat catch was observed.
