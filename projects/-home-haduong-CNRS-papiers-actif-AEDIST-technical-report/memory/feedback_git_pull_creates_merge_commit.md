---
name: git-pull-creates-merge-commit
description: git pull on diverged local main creates a merge commit that violates protected-branch rules — use fetch+reset or rebase
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f52dcfd1-cee6-4aad-8ca8-dbe7ff3ba0fb
---

Never run `git pull origin main` when local main has diverged from origin/main (i.e., local has commits not yet on origin). Git creates a merge commit, which GitHub's branch protection ("must not contain merge commits") rejects on push.

**Why:** Happened during 2026-05-23 healthcheck session: local main had housekeeping commits, origin had 3 new PR merges; `git pull` merged both sides. Push was rejected. Required `git reset --hard origin/main` and rerouting changes through a PR.

**How to apply:** Before pulling, check divergence: `git rev-list --left-right --count main...origin/main`. If local main has commits ahead (left > 0), do NOT `git pull`. Instead: stash or branch the local commits, then `git fetch && git reset --hard origin/main`, then cherry-pick onto a branch.
