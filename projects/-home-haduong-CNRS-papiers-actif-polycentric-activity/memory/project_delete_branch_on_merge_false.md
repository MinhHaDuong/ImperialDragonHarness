---
name: project-delete-branch-on-merge-false
description: "MinhHaDuong/polycentric_activity has delete_branch_on_merge=false on GitHub — every merged PR leaves its remote branch behind, requires manual deletion."
metadata: 
  node_type: memory
  type: project
  originSessionId: bc2349a2-725b-4756-8875-771442f0f763
---

Confirmed 2026-07-07 (`gh api repos/MinhHaDuong/polycentric_activity --jq
.delete_branch_on_merge` → `false`) after two merged PRs (#3, #4/#5 chain)
left stale `origin/<branch>` refs that `git branch -vv` kept showing as
remote-only until manually deleted.

**Why:** matches the git.md-documented `cired.digital` pattern — this repo
is the same shape, not the exception. `gh pr merge --delete-branch` does not
override a repo-level `false` setting either.

**How to apply:** after every `gh pr merge` in this repo, follow with
`git push origin --delete <branch>` and, once confirmed merged
(`git merge-base --is-ancestor <branch> origin/main`), `git branch -D
<branch>` locally. Don't assume the merge alone cleaned up — verify with
`git branch -a` / `git fetch --prune` before calling a session's hygiene
sweep done.
