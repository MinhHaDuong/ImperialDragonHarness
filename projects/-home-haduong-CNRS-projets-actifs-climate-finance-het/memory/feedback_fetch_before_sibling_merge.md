---
name: feedback_fetch_before_sibling_merge
description: "In a multi-PR wave editing the same file, fetch immediately before each sibling merge and grep-verify the content union after — a stale origin/main ref silently drops just-merged siblings' additions"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 2f6c6c7e-67d0-4265-a5f7-bfdc0a1ccdd1
---

When merging several PRs of a wave that all touch one file (e.g. three
manuscript PRs each editing `content/manuscript.qmd` + `main.bib` +
`test_manuscript_prose.py`), integrate them one at a time and **`git fetch origin`
right before each `git merge origin/main`**. If you merged sibling #N with `gh pr
merge` but did not fetch before merging origin/main into sibling #N+1, your local
`origin/main` ref is stale — it lacks #N's merge commit — so the merge silently
produces a result missing #N's non-conflicting additions (looks like a clean
auto-merge, no conflict reported for that file).

**Why:** the drop is invisible. `git merge` reports "Auto-merging <file>" and
exits 0; only the *content* is wrong. Caught 2026-07-08 (raid on 0141 children,
PRs #909/#910/#911) only because I grepped the merged `main.bib` for the three
new `@key`s and found 1 of 3, then found the manuscript had lost #910's
`@unfccc2010cancun`/`@aosis2024ncqg`/`@unfccc2009copenhagen` in-text cites too.

**How to apply:**
1. Before every sibling merge: `git fetch origin` (cheap; the git.md "rebase at
   every gate" rule, applied to merges).
2. After resolving conflicts, **grep-verify the union before committing** — every
   sibling's citations/keys/tests present exactly once, plus prior siblings'
   landmarks (e.g. `grep -c '@unfccc2010cancun' manuscript.qmd`). Do not trust a
   clean auto-merge.
3. If a drop is found, don't hand-patch the merge — `git checkout origin/main --
   <file>` (known-good, carries the merged siblings) and re-layer only *this*
   PR's small change on top. Then re-verify.

Force-push is denied in this repo, so integrate with `git merge origin/main` into
the branch (merge commit), not rebase. Extends [[feedback_no_rebase_dvc]];
merge-side analogue of the rebase drop-cascade.
