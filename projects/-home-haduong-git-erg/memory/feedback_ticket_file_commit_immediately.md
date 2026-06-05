---
name: feedback_ticket_file_commit_immediately
description: Ticket files created as untracked files in the main repo strand on branch switches — commit or embed in agent prompt immediately
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8c52a371-c7aa-450c-9d12-1d9615d43926
---

Ticket files written to the main repo's working tree as untracked files are fragile: they strand when the branch switches and cannot be staged through the gitignore from a reset cwd (the explore-worktree path is gitignored).

Two recovery paths:
1. Commit the ticket file onto a branch immediately after creating it.
2. Embed the ticket content directly in the execute agent's prompt — the agent creates the file as its first step.

**Why:** During the 0200 raid, the ticket was written to the main repo but got stranded when the branch switched to t0201. The gitignore for `.claude/worktrees` also blocked staging from the hook-reset cwd.

**How to apply:** After `Write`-ing a ticket file to the repo, immediately stage and commit it onto the current branch before launching the execute agent. If the cwd will be reset by a hook, use `git -C` with the absolute worktree path or embed the content in the agent prompt as a fallback.
