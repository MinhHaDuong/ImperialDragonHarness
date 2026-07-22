---
name: feedback-optimistic-concurrency-ticket-ids
description: "Author rejected ID-reservation machinery for erg tickets — optimistic concurrency only; collision = renumber to next free ID, detected by erg check in CI"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f2d5c6fe-e355-4bbd-a8e7-8cba453c7d7b
---

Author decision (2026-06-04, after three same-day ID collisions): no reservation machinery for ticket IDs — not in the `erg` binary, not in the `ticket-new` skill. "In the subway if the seat is taken move to the next one." KISS.

**Why:** Collisions are rare and cheap to fix (rename to next free ID, one commit); a reservation system (remote refs, push side effects) adds failure modes worse than the disease. git-erg#282 closed wontfix; ticket 0427 closed wontfix.

**How to apply:** Keep allocating optimistically (`erg new` after a fetch — the interim fetch-first habit stays, see [[feedback-ticket-id-collision-check]]). On collision at merge time: renumber, don't redesign. Detection belongs to `erg check` in CI (ticket 0418). Do not re-propose reservation/locking for ticket IDs.

**Wrinkles from raid 541+543 (2026-06-12, double collision 0549→0550→0552):** (1) `git commit -am` does NOT stage a freshly-created untracked `.erg` — the ticket reference then points at a phantom file (caught by verify-gate as a REROLL); `git add` the new ticket explicitly. (2) Scanning origin/main is not enough on a busy night — sibling sessions' unmerged branches hold claimed IDs; scan all remote branches (`git branch -r` + `ls-tree`) before renumbering, and expect `erg check` in CI to be the final arbiter after rebase.
