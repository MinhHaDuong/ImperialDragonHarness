---
name: feedback-erg-close-bookkeeping-conflict
description: "Two parallel erg closes conflict in a THIRD ticket's Blocked-by bookkeeping; keep both note lines, drop both headers"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d1557082-ceb0-4d01-98e8-47f3a8cd1b5e
---

When two tickets that both block a third ticket are closed in parallel (one on main, one on a PR branch), the rebase conflicts in the THIRD ticket's file — not in either closed ticket. `erg close` removes the corresponding `Blocked-by:` header and appends a "blocker NNNN closed — Blocked-by removed" log line to every dependent ticket, so both sides edit the same adjacent lines.

**Why:** erg's close-time bookkeeping fans out to dependent tickets; parallel closes of sibling blockers therefore collide on the shared dependent even though the closed tickets themselves are disjoint files. Observed raid 419-420 (2026-06-04): closing 0412 (on main) and 0419 (PR #712) both edited 0413.

**How to apply:** Resolve by keeping BOTH log note lines (chronological order) and removing BOTH `Blocked-by:` headers — the merged ticket keeps only still-open blockers. Run `tickets/erg check tickets/` before `git rebase --continue`. Related: [[feedback-erg-pr-merge-partial-success]].
