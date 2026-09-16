---
name: feedback-ratchet-ceiling-race-and-dropped-close
description: "Ratchet data files (emdash_ceiling.txt) race with parallel prose merges; a post-queue rebase can drop erg-pr-merge's close commit — verify ticket state on origin/main before re-closing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2d166e90-6882-414f-8eb9-e0a16755dbc2
---

Two related races observed in raid 552 (2026-06-12, PR #1022):

1. **Ratchet ceilings race with parallel prose merges.** A committed ratchet
   value (e.g. `tests/data/emdash_ceiling.txt`) initialized on the branch goes
   stale the moment a parallel manuscript PR (here #1023, +3 em dashes) merges
   first. The fix is a documented re-init commit on the rebased final text —
   expected behaviour, not a defect.
2. **Post-queue rebase can drop the erg-pr-merge close commit.** After
   `erg-pr-merge` pushes the close commit and queues auto-merge, a rebase to
   fix the ratchet rewrote the branch and the merged tree had the ticket still
   open; a separate chore PR (#1024) re-closed it.

**Why:** Without checking, the orchestrator could hand-close an
already-re-closed ticket or panic about a "lost" close.

**How to apply:** After any merge that involved a post-queue rebase, verify
ticket state with `git cat-file -e origin/main:tickets/closed/<file>` before
acting. Related: [[feedback-rebase-drop-cascade]],
[[feedback-erg-pr-merge-partial-success]].
