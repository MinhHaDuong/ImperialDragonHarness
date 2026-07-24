---
name: feedback_merge_conflict_all_hunks
description: "When scripting a merge-conflict resolution, process every hunk and run the validator before pushing — a first-match-only regex let raw conflict markers land on main"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 63b53dc0-97f6-44a6-8e47-3b0a129fbc06
  modified: 2026-07-23T15:25:24.980Z
---

Scripted conflict resolution on ticket files (PRs #1099/#1100, 2026-07-23): a
`re.search` (first match only) resolved hunk 1 and silently left hunk 2's raw
`<<<<<<<` markers in the committed merge, which then landed on main; caught
only by the next `erg check`. Also unioned Blocked-by header lines both sides
had *removed* (blockers closed) — for removals, union is the wrong lattice.

**Why:** merge conflicts can have multiple hunks per file, and log-append vs
header-removal hunks need opposite resolutions (union vs intersection).

**How to apply:** use `re.finditer`/loop over ALL conflict hunks; after
resolving, `grep -c '<<<'` must be 0 AND the domain validator (`erg check`,
tests) must pass BEFORE committing the merge; union log lines, but for
header lines removed by either side, keep the removal.
