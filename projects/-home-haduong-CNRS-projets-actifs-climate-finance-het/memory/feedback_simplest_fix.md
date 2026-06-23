---
name: Simplest fix first
description: Don't add hooks/exceptions when the existing design already works — use it
type: feedback
---

When a hook blocks an operation, don't add exceptions or new hooks to work around it. Ask whether the operation itself can be changed to work within the existing rules. Example: `git merge --no-ff` creates a commit on main (blocked by pre-commit), but `git merge` (fast-forward) moves the pointer without committing — no hook fires, no loophole needed.

**Why:** User challenged a pre-merge-commit hook + dvc.lock exception as unnecessary complexity. The existing branch-in → commit → fast-forward-out pattern already works within the hooks.

**How to apply:** Before adding hook exceptions or new hooks, check if the operation can be restructured to avoid triggering the hook at all.
