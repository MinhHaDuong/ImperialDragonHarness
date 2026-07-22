---
name: feedback-rtk-log-hides-merge-commits
description: "rtk-filtered `git log --oneline` omits merge commits — verify tips with rev-parse or `rtk proxy git log` before diagnosing divergence"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ed2a7ca2-6871-43e3-a72e-54b937128ca3
  modified: 2026-07-22T16:40:34.649Z
---

Under the rtk rewrite hook, `git log --oneline` silently drops merge commits
from its output. Observed 2026-07-22 (0263 close session): `rev-parse
origin/main` gave 79c65026 (a PR merge commit) while `git log -1` displayed
e1b847e8, its first parent — looking like a stale ref or divergence when the
checkout was in fact current.

**Why:** rtk's token-saving filter treats merge commits as noise; the log it
returns is not the true first-parent history. Any conclusion about "which
commit is the tip" or "is X an ancestor" drawn from rtk log output can be
wrong.

**How to apply:** when merge topology matters (verifying a branch is current,
diagnosing divergence, confirming a PR merge landed), trust `git rev-parse`
/ `git merge-base --is-ancestor` (exit codes, unfiltered), or view the real
log with `rtk proxy git log --oneline`. Never diagnose a ref mismatch from
rtk-filtered log text alone.
