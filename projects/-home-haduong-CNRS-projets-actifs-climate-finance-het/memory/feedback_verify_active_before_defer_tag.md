---
name: feedback_verify_active_before_defer_tag
description: "Before a bulk defer-tag / triage pass, fetch origin/main and verify no ticket is being actively worked by a parallel session"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ea1cbb06-91f7-47d0-98e2-86ddd1fab4bd
---

During a ticket audit under parallel sessions, do NOT tag a ticket `deferred` (or close/renumber it) on the strength of a stale read. Fetch `origin/main` first and check whether the ticket is being actively worked elsewhere.

**Why:** In the 2026-07-10 layout audit I deferred 0221/0222/0218 as "non-blocking hygiene" — but the data axis was *en cours*: a parallel session had 0222 landing on main and was executing 0221's children. Deferring them would have hidden active work from `erg ready`. The author's own words ("données (en cours)") were the tell I initially overrode. Same session, a freshly-created ticket collided on ID 0227 (git-erg optimistic allocation, #282) with the parallel session's 0227 — caught only at merge, renumbered to 0229.

**How to apply:**
- Before a bulk label/close/renumber pass: `git fetch origin && git log --oneline HEAD..origin/main` — scan for commits touching the tickets you're about to triage.
- A ticket the author calls "en cours" is active — never defer it, even if an audit agent flags it "non-blocking hygiene." Agent staleness verdicts are advisory; the live branch + the author's framing are authoritative.
- After creating tickets under parallel sessions, `erg check` for duplicate IDs and renumber on collision (fix cross-refs) — seat taken, move to the next.

Related: [[feedback_fetch_before_sibling_merge]] (merges silently dropping siblings' additions), [[feedback_parallel_work]] (check the filesystem, don't assume staleness), [[project_repo_layout_decision]] (the audit this came from).
