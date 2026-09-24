---
name: harness-main-blocked-by-memory-edits
description: "~/.claude's primary checkout stalls behind origin/main because memory is written there uncommitted; reconciled by hand 2026-09-23 (165 commits), structural fix is harness ticket 0972"
metadata:
  node_type: memory
  type: project
  originSessionId: b87a9f19-6e44-43d9-a91e-3488202c9aa2
  modified: 2026-09-23T10:28:23.823Z
---

The harness is live from `~/.claude` itself, on `main`. Memory files are written
straight into that checkout (the only place the write guard allows), and they are
also changed upstream by merged PRs (`/dream` consolidations restructure MEMORY.md
indexes). So `scripts/sync-local-main.sh` refuses to fast-forward, and nothing
merged reaches running sessions. On 2026-09-23 it was 165 commits behind:
harness PR #968 (forked skills pinned to sonnet) was merged but not live.

Reconciled that day by hand: backup of every modified and untracked file (tar +
patch under the session scratchpad), restore the six modified files, `merge
--ff-only`, `git apply -3` the local patch. Three MEMORY.md indexes conflicted.
Two were plain list appends (union, dedup by link target). The climate-finance-het
index had been restructured upstream into Key insights / Entries, so a union
duplicated the old sections; the right resolution was the new layout plus only the
lines the local patch added, not the old lines upstream had removed.

**Why:** a stale live checkout silently voids every harness merge; a union of a
restructured file silently duplicates.

**How to apply:** after any harness merge, check `git -C ~/.claude rev-list
--left-right --count main...origin/main`; when it is behind and dirty, reconcile as
above, and for a conflicted index take the incoming layout plus the local patch's
own `+` lines. Structural fix: harness ticket 0972. Related: [[harness-gate-and-breaker]] (ticket 0954, PR #967).

**Fixed 2026-09-24 by harness PR #1011 (ticket 0972 closed).** The sync now
absorbs a colliding file that is byte-identical to the incoming one, and a
`memory/MEMORY.md` whose local edit only added lines (incoming index + local
additions, left uncommitted). Other dirt still refuses, naming its paths. So
landing local memory through a PR no longer stalls the next sync; the manual
recipe above is only for genuine divergence.

Recurred on padme 2026-09-24: 150 commits behind, with `scripts/scoped-check.py`
missing, so a lane's `make check-diff` had to borrow a harness worktree. The only
colliding path was a local log line on harness ticket 0207, closed and moved
upstream. Restoring that one file let `merge --ff-only` pass with the other dirty
memory files in place: ff tolerates dirty paths upstream did not touch.
