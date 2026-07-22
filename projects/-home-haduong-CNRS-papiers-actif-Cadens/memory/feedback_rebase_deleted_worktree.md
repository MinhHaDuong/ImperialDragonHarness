---
name: Rebase after worktree deletion
description: How to recover a rebase when the worktree has been cleaned up mid-rebase
type: feedback
originSessionId: 551816f0-27aa-4176-b984-5bc0b6672a18
---
When a worktree is deleted mid-rebase (e.g., by session restart), the local branch may also be gone. But the commits are still in the git object store via the remote tracking ref (`origin/<branch>`). Recovery:

1. `git log --oneline origin/<branch>` — confirm commits are accessible
2. `git worktree add /tmp/<name> -b <new-branch> origin/main` — fresh worktree from current main
3. `git cherry-pick <commit1> <commit2> <commit3>` — replay commits in order onto new branch
4. Resolve conflicts (same pattern as a rebase), `git cherry-pick --continue --no-edit`
5. Push new branch, create new PR

**Why:** `gh pr merge` returning 405 "not mergeable" means dirty (conflicts), not a worktree issue. The worktree conflict error from `gh pr merge` is different — that one is fixed by `gh api -X PUT .../pulls/N/merge`.

**How to apply:** Whenever a rebase is interrupted by session end, check if the worktree still exists before trying to resume. If gone, use the cherry-pick recovery flow above.
