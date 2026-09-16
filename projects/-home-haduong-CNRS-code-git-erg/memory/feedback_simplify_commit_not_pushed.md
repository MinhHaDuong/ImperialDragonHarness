---
name: feedback-simplify-commit-not-pushed
description: "/verify's simplify fixes may not reach the PR branch — always confirm with git log on the remote before merging"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0bf1ac7d-829a-48b8-833c-94a12f02f0ab
---

The /verify skill runs /simplify and reports "N fixes applied", but those fixes may be committed to a throwaway worktree and never pushed to the PR branch. In PR #191 (0170), simplify claimed to add `os.IsExist(err)` — the exact same fix Copilot later flagged. The fix wasn't on the remote branch.

**Why:** /simplify applies edits and commits them in the skill's working context, but does not automatically push. If /verify runs in a transient worktree, the commit is lost when the worktree exits.

**How to apply:** After /verify reports simplify fixes, run `git log --oneline origin/<branch> -5` before merging to confirm the simplify commit is on the remote. If it's absent, apply the fixes manually.
