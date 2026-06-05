---
name: feedback-precommit-hook-commit-ordering
description: "Pre-commit adherence hook runs the working-tree test suite against the index — order multi-commit series so every intermediate index state passes; use `git commit -- <paths>` to slice"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f2d5c6fe-e355-4bbd-a8e7-8cba453c7d7b
---

The pre-commit hook runs `pytest -m adherence` from the **working tree** against the **index** at each commit. A new guard test sitting in the working tree (even unstaged) is executed and sees `git ls-files` of the index.

**Why:** During 0417, a 3-commit series (rule fix → deletions → test) failed twice: the guard test in the working tree was red until the `git rm` deletions entered the index, so the first commit bounced; an earlier attempt silently swept pre-staged deletions into the wrong commit.

**How to apply:**
- Order commits so each intermediate index state keeps the working-tree suite green (deletions a guard depends on come FIRST).
- Slice precisely with `git commit -m "..." -- <paths>` (commits the working-tree state of those paths regardless of what else is staged) instead of relying on the staging area accumulated by earlier `git add`/`git rm`.
- If the series can't be ordered green, collapse to one atomic commit rather than fight the hook.
