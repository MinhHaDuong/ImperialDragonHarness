---
name: feedback-worktree-edit-paths
description: "Edit tool uses absolute paths — edits go to main repo, not active worktree, when paths point to ~/chemin-de-voix/"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 822c9c51-c25f-4231-9efb-cb69dd291453
---

When working in a worktree at `.claude/worktrees/fix-pipeline-keys`, the Edit tool with path `/home/haduong/chemin-de-voix/scripts/foo.py` edits the **main repo** file, not the worktree copy. Commits made via `cd ~/chemin-de-voix && git commit` also land on the main repo's branch (master), not the worktree branch.

**Why:** Edit tool uses absolute paths verbatim. Worktree files live at `.claude/worktrees/<name>/scripts/foo.py`. The main repo files live at `~/chemin-de-voix/scripts/foo.py` — same absolute path, different git HEAD.

**How to apply:** When in a worktree, always use paths relative to the worktree root, e.g. `/home/haduong/chemin-de-voix/.claude/worktrees/<name>/scripts/foo.py`. Or use `git -C <worktree-path>` for git commands. The `pwd` output confirms the cwd; ensure bash commands and Edit paths are consistent with it.

Recovery if commits land on wrong branch: cherry-pick the commits to the worktree branch, then rebase to drop duplicates before pushing the PR branch.
