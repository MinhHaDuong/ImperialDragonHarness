---
name: gh-resolves-repo-from-cwd
description: "A bare `gh pr edit N` run from a scratch directory inside another git repo edits that repo's PR N; pass -R on every gh mutation issued outside the project worktree"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6d767542-7121-4b6a-b5bb-36be109cd846
  modified: 2026-09-02T10:26:55.625Z
---

On 2026-09-02 a `cd $CLAUDE_JOB_DIR/tmp && gh pr edit 177 --body-file …`
overwrote the body of ImperialDragonHarness PR #177 (a merged, unrelated PR):
the job scratch directory lives under `~/.claude`, which is the harness repo,
and `gh` resolves the repository from the cwd's git remote. Recovered from the
PR's `userContentEdits` GraphQL history (the earlier node's `diff` is the
previous body) and restored with `gh pr edit -R`.

**Why:** the failure is silent and lands on someone else's record; the URL
`gh` prints is the only tell, and it comes after the write.

**How to apply:** any `gh` command that mutates (pr edit/close/comment/merge,
issue edit, api -X POST) issued from a cwd that is not the project checkout
carries `-R owner/repo` explicitly, and the printed URL is read back before
moving on. Scratch directories under `~/.claude/jobs/` are inside a git repo.
Related: [[execute-authorized-outward-actions]].
