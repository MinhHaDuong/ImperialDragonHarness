---
name: merge-auto-boundary-races
description: "erg-pr-merge post-close recompute race is FIXED (IDH 0200 closed); script self-recovers; one residual trap: direct-merging a PRE-close bounce skips the ticket close"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 28935cc7-f899-4c7d-abd7-a4079017615a
---

HISTORY: `gh pr merge --auto` used to bounce on GitHub's post-push
mergeability recompute after the close commit, needing a manual
`gh pr checks --watch` + plain `gh pr merge` recovery (10 confirmed
cases, raids of 2026-06-04). IDH ticket 0200 (closed, IDH PR #283)
hardened the script: it now waits for mergeability to settle and
retries once on its own — observed 3/3 clean on 2026-06-05 (git-erg
PRs #285, #287, #288). No manual recovery needed anymore unless the
script's own retry fails.

**Residual trap (cost: one extra PR, #279/#281):** if the script
bounces BEFORE its close step (e.g. "CI has 1 check(s) still
running") and you recover with plain `gh pr merge`, the merge
succeeds but the ticket close is silently SKIPPED. Re-run the script
instead (pre-close it has done nothing and is safe to retry). After
any direct-merge recovery, verify with
`git ls-tree origin/main tickets/ | grep <id>` — if the ticket is
still open, land close+archive via a tiny lifecycle PR.
