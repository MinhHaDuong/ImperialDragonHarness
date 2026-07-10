---
name: feedback-force-push-denied-rebuild-clean
description: "When the session denies force-push, don't fight it — rebuild the stale branch cleanly on current main (new branch, copy deliverables, fresh commit, ff push)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: abeb176f-22ca-461f-bb52-7bdffd08f43b
---

2026-07-08, RR session. After rebasing a feature branch onto main it diverged from origin and needed `git push --force-with-lease` — the session permission layer denied the force-push twice. Retrying verbatim is futile.

**Why:** A rebased branch can only be pushed with force. If force-push is blocked, the branch is stuck. But the goal (landing the deliverables on main) does not require force-push.

**How to apply:** Instead of rebasing + force-pushing a stale branch, rebuild it clean: `git worktree add <path> -b <newbranch> origin/main`, `git checkout <oldbranch> -- <deliverable files>` to bring the content over, re-apply any small edit that depends on current main (e.g. a hygiene-list addition on top of main's version), commit, push (fast-forward, no force), open a fresh PR, close the old one. Also: to land a small change on an *unmerged* PR branch without rewriting history, add a NEW commit and normal-push (`git push origin HEAD:<branch>`) — never rebase+force. And erg-pr-merge appends a close commit + normal push, so atomic merges never need force either. See [[feedback_no_rebase_dvc]] and [[project_worktree_env_data]].
