---
name: feedback_shared_worktree_concurrent_merge_collision
description: "A shared worktree during concurrent merge recovery is a collision surface — a session's local commits can be silently orphaned when a peer session advances the same branch tip"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f6a59d05-fc03-4ef4-8906-2e4ae1c5323b
  modified: 2026-07-28T20:31:54.840Z
---

On PR #1284 (ticket 0565), a round-2 review-fix commit was made locally in a
worktree shared with another session working the same branch. Before it could
be pushed, the branch tip advanced under it — a ticket-log-bump commit
(`79809270`) and then `erg-pr-merge`'s close-commit cherry-pick (`57f14b9d`)
both landed on the same ref from the other session's activity. The local
review-fix commit was never an ancestor of the new tip, so a plain push would
have rejected it and a force-push would have silently dropped it — either way
it would not have reached `origin` and the merge would have shipped without
it.

Recovery: cherry-pick the orphaned commit onto the pushed tip from a
**throwaway** worktree, leaving the in-flight session's shared worktree
untouched. This is the same shape as `rules/git.md`'s "multi-PR wave on one
file" fetch-before-merge rule and the "anchor branch-mutating git across a
forked-skill boundary" rule, but the trigger here is a peer *session*
advancing a *shared* branch checkout mid-edit, not a stale `origin/main` ref
or a worktree-switching tool boundary.

**When two sessions occupy the same worktree on the same branch during an
active merge/review cycle, treat every local commit as at-risk until pushed.**
Before adding a commit in a shared worktree, check whether the branch tip
already moved past your last known HEAD (`git log --oneline @{u}..HEAD` vs.
what you expect); after committing, push immediately rather than batching
several local commits, since each one you hold locally is a window for a
concurrent `erg-pr-merge` or sibling session to advance the ref underneath it.
If a commit turns up missing from `origin` after a merge, `git reflog` /
`git fsck --lost-found` in the same checkout usually still has it — cherry-pick
from a disposable worktree rather than editing the shared one further.

Related: [[feedback_merge_conflict_all_hunks]], [[feedback_verify_agent_worktree]].
