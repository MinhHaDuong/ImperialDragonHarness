---
name: stale-duplicate-tickets
description: Long-running PRs that include a close-and-archive commit can reintroduce open copies of already-archived tickets when they base on stale main.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab5e5447-d280-4bd4-b5f3-9b0f3f0d028e
---

The open+closed cross-directory duplicate broke CI three times in one session:

- PR #215: tickets/0181 stale open copy on main
- t0196 branch: tickets/0188-0193 reintroduced by the 0194 close-and-archive commit
- Repeated on a second pass

**Why:** The 0194 PR's `ticket(0194): close and archive` commit was authored while
main still had those files in `tickets/` (before the raid archived them). When
merged, the commit silently reintroduced them into the open directory.

**How to apply:**
- Before merging any PR whose diff includes ticket files in `tickets/` (not
  `tickets/closed/`), run `erg check` locally to catch cross-directory duplicates.
- When a close-and-archive commit is part of a long-running PR, rebase it onto
  the current main just before merge and re-verify the ticket corpus.
- Ticket 0198 adds the missing test canary for this pattern.

See also: [[ascii-only-src-go]] (another class of CI surprise caught post-merge)
