---
name: feedback_helper_agent_needs_own_worktree
description: "An Agent launched without isolation inherits the parent's worktree pin — it cannot reach other worktrees and can wreck the parent's"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 36288e08-760c-498d-809d-4ea0d872d521
  modified: 2026-09-23T18:58:06.460Z
---

Launch every helper agent that touches git with `isolation: "worktree"`. Without it, the child inherits the parent session's worktree pin: it cannot `git -C` into another worktree (a merge helper was refused outright), and whatever it checks out or edits lands in the parent's tree. On 2026-09-23 a /gaze agent launched without isolation checked out the PR branch in the orchestrator's worktree and left a half-done refactor there when stopped; salvaged as a patch, then restored.

**Why:** the worktree guard pins Bash to one tree per session and its children; `EnterWorktree(path=…)` inside the child did not re-root Bash.

**How to apply:** read-only reviewers too, if they run git. To merge an agent's PR from the orchestrator, see [[reference_merge_from_foreign_worktree]].

**Merged from `reference_merge_from_foreign_worktree.md` (2026-09-25):** To merge an agent's PR: in your own worktree git switch --ignore-other-worktrees <branch> && git merge --ff-only origin/<branch>, run erg-pr-merge -C <own worktree> <PR>, then git switch --detach origin/main (staying on the branch leaves the agent's tree looking dirty and blocks worktree-gc).
