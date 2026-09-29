---
name: feedback_adjacent_blocked_by_lines_conflict
description: Two PRs that each close a blocker of the same ticket remove adjacent Blocked-by lines and add adjacent log lines there, so the second one goes DIRTY and its auto-merge waits forever
metadata:
  type: feedback
---

2026-09-29: #1061 closed 0984 and #1060 closed 0987; `erg close` in each removed
its own `Blocked-by:` line from 0985 and appended a "blocker closed" log line.
After #1061 merged, #1060 went `DIRTY`: GitHub runs no checks on a conflicting
branch, so the queued auto-merge showed nothing but "pending" until the author
asked "Stuck or what".

**Resolution:** rebase, drop both `Blocked-by` lines (both blockers are closed),
keep both log lines in time order (append-only), `erg check`, then run the full
gate on the rebased union before pushing.

**How to apply:** when sibling PRs close tickets that block the same dependent,
merge them one at a time and re-check `mergeStateStatus` after each; a wait loop
must also stop on `DIRTY`, not only on `MERGED`.
Related: [[feedback_verify_sibling_prs_jointly]].
