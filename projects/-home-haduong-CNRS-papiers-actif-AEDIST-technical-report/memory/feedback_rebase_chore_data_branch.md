---
name: feedback-rebase-chore-data-branch
description: Mixing ticket housekeeping and data commits on the same base branch causes dense rebase conflicts at merge time
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7b49cd36-1e93-49e7-bc96-bec4c4aad2dd
---

Don't put data commits (CSV regeneration, scoring runs, figure rebuilds) on a "chore/" base branch that also accumulates ticket-lifecycle commits. When a feature branch targets such a chore base, every rebased commit conflicts against the data files.

**Why:** The raid-290-192-313 chore branch accumulated 10 commits spanning ticket notes, data scoring (sota_cross_eval.csv), and manuscript edits. Rebasing onto main required resolving 8 consecutive conflicts in ticket logs and the CSV — all mechanical but time-consuming.

**How to apply:** Data commits (scored CSVs, regenerated figures, arm_flat re-extractions) belong on short-lived feature branches targeting main directly. Ticket-lifecycle commits (notes, closures, unblocks) can go direct to main per workflow.md exception. Keep chore/* branches for coordinated multi-ticket releases, but don't mix data work into them.
