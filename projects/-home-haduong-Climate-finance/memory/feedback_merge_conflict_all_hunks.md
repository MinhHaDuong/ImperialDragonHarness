---
name: feedback_merge_conflict_all_hunks
description: "When scripting a merge-conflict resolution, process every hunk and run the validator before pushing — a first-match-only regex let raw conflict markers land on main"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 63b53dc0-97f6-44a6-8e47-3b0a129fbc06
  modified: 2026-07-28T13:00:41.451Z
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

**Predict the union before merging, don't only grep after.** A clean
`mergeStateStatus` says "no conflict", never "your change survived" — a
sibling PR that regenerated a shared artifact from a stale base can revert a
fix without any conflict. `git merge-tree --write-tree <base> <head>` performs
the 3-way merge in memory and prints a tree, so the merged content is
inspectable *before* you merge:

```bash
T=$(git merge-tree --write-tree origin/main origin/pr-NNNN)
git cat-file blob "$T:path/to/artifact" | grep -c 'the-marker-you-need'
```

Used on PR #1141 (2026-07-27), whose head carried a `codebook.md` missing the
`\|` escape merged hours earlier: merge-tree predicted the escape would
survive (that branch touched only a different row), and merged main confirmed
it. Survival was line disjointness, not protection — so still grep after the
merge; merge-tree tells you in advance whether to expect trouble.

**Resolve inside the conflict hunks; never rebuild the file from one side.**
The tempting shortcut when several paragraphs conflict is to take one side's
*whole file* as the base and re-apply the other side's paragraphs onto it.
That silently reverts every change git had already **auto-merged** outside the
hunks — the regions with no conflict markers, which is exactly where you stop
looking. On PR #1258 (2026-07-28) this dropped two calibrated sentences in the
abstract and §1 that the auto-merge had placed correctly; the marker count
caught it, reading the resolved paragraphs would not have. Regenerate the
conflict (`git checkout -m -- <file>`) and substitute hunk-by-hunk with
`re.subn` over `<<<<<<< ours\n(.*?)=======\n(.*?)>>>>>>> theirs\n`, asserting
the replacement count. Note the marker labels differ by route: a fresh `git
merge` writes `HEAD` / `origin/<branch>`, `git checkout -m` writes `ours` /
`theirs` — a regex pinned to one silently matches zero hunks under the other.

Verify by **counting each side's markers in the composed file**, not by
reading the diff: list every phrase each side contributed plus every phrase
that must be absent, and assert exact counts (13 present / 4 absent on #1258).
A count is the only check that sees a silent revert in a region you never
opened.
