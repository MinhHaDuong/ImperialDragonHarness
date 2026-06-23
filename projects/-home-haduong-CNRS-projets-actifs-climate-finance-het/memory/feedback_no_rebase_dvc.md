---
name: No rebase with DVC symlinks
description: Use git merge (not rebase) when DVC-tracked symlinks show as unstaged changes
type: feedback
---

Never use `git rebase` in this repo — DVC-tracked symlinks in `data/catalogs/` show as unstaged changes that block rebase. Use `git merge` instead, with `git stash`/`git stash pop` around it if needed.

**Why:** DVC replaces tracked files with symlinks to its cache. After `dvc pull`, these symlinks point to new targets, which git sees as modified files. `git rebase` refuses to proceed with unstaged changes and `git checkout` can't fix DVC symlinks.

**How to apply:** When merging branches or pulling, always use `--no-rebase` / `git merge`. If DVC files block the merge, stash first: `git stash && git merge ... && git stash pop`.
