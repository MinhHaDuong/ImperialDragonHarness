---
name: squash-merge local-master sync via rebase
description: After a squash merge, use git rebase origin/master — absorbed commits are skipped automatically; reset --hard is blocked by the guard hook anyway
type: feedback
originSessionId: 080a3080-7ae1-4d9f-ae68-ed41d6c9c03c
---
After squash-merging a PR, sync local master with `git rebase origin/master`. Git detects that the patch content of each local commit is already upstream and skips them cleanly ("le contenu de la rustine est déjà en amont"). No cherry-pick gymnastics needed when all local commits are absorbed by the squash.

**Why:** The guard hook (`guard-destructive-bash.sh`) blocks `git reset --hard`, and rebase is the right default anyway — it handles both cases: skips absorbed commits, replays genuinely new ones, and surfaces conflicts explicitly if something unexpected lands.

**How to apply:**
1. Ensure working tree is clean (`git status --short`).
2. `git fetch origin && git rebase origin/master`.
3. Git skips commits already in the squash; replays anything genuinely new.
4. If a conflict appears, it means a local commit was NOT absorbed — resolve normally.

**Edge case — stale-only local commits:** If the only local commit is a stale STATE.md housekeeping update that is immediately superseded by the upstream changes, `git branch -f master origin/master` is cleaner than rebase (it just discards the stale commit rather than replaying it on top of the new history). Use rebase when local commits have genuine value; use `branch -f` only when the local-only commit is purely ephemeral and the user confirms it's safe to drop.

**Earlier wrong approach (do not use):** reset --hard + cherry-pick. Blocked by the guard hook.
