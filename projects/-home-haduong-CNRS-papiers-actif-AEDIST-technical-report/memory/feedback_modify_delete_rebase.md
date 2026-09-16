---
name: feedback-modify-delete-rebase
description: "When a parallel commit deletes a file that the branch modifies, rebase creates a modify/delete conflict — accept the deletion but manually migrate the meaningful new content to the surviving location."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba2d67f0-75cd-40df-9a2d-f526a12356d8
---

When rebasing a branch that modified a file (e.g. `report/exp2-analysis.mk`) against a main that **deleted** that file, git creates a "modification/deletion" conflict. The correct resolution:

1. `git rm <file>` — accept the deletion.
2. Identify which new content from that file must survive (new build targets, new prerequisites).
3. Manually add that content to wherever it belongs now (e.g. root `Makefile`).

**Why:** This happened with ticket 0348: `d3cf027f` deleted `report/exp2-analysis.mk` as part of a build refactor (PR #609, "collapse Exp2 build to single producer") while 0348 was in flight adding a new figure target to the same file. The resolution was to move the `fig_spider_cross_exp` build rule directly to the root Makefile.

**How to apply:** Before starting any ticket that modifies a Makefile or `.mk` file, check `git log --oneline HEAD..origin/main` for refactor commits that might delete or restructure build files. If found, reconcile first — it's cheaper than resolving a mid-rebase conflict.
