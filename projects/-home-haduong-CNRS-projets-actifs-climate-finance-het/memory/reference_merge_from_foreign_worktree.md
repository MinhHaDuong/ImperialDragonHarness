---
name: reference_merge_from_foreign_worktree
description: "Merging a PR whose branch is checked out in another agent's worktree, from a guarded session — and the stale-tree side effect"
metadata:
  node_type: memory
  type: reference
  originSessionId: 36288e08-760c-498d-809d-4ea0d872d521
  modified: 2026-09-23T18:58:11.010Z
---

Recipe used all day on 2026-09-23 (#1455, #1457–#1467): in the session's own worktree, `git fetch origin && git switch --ignore-other-worktrees <branch> && git merge --ff-only origin/<branch>`, then `~/.claude/skills/merge/erg-pr-merge -C <own worktree> <PR>`, then `git switch --detach origin/main`. Do not stay on the branch: moving a branch ref under another worktree leaves that tree's files at the old commit, so it reads as "uncommitted WIP" and `worktree-gc.sh` refuses to remove it (seven held worktrees that evening).

The PR body must name its ticket by path (`**Ticket:** tickets/0871-<slug>.erg`); a bare ID is rejected by erg-pr-merge. Edit the body with `jq -n --rawfile body f '{body:$body}' | gh api repos/<o>/<r>/pulls/<N> -X PATCH --input -` and read it back.

Related: [[feedback_helper_agent_needs_own_worktree]].
