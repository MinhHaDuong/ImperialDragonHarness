---
name: Decide the branch before editing
description: Always checkout the target branch before touching any file — never edit on main then move changes
type: feedback
---

Decide the target branch BEFORE editing any file. Never edit on main's working tree then scramble to move changes via worktree copy.

**Why:** Editing on main then realizing you can't commit there leads to wasteful worktree gymnastics (create worktree, copy file, commit, clean up). Root cause analysis showed this happens when the agent treats an edit as standalone rather than connecting it to the right branch first.

**How to apply:** At conversation start, on-start.md now creates an explore branch eagerly. For mid-conversation edits, always verify `git branch --show-current` before touching files. If on main, branch first.
