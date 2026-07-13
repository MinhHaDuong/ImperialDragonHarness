---
name: worktree-path-trap-needs-guard
description: Prompt warnings do not prevent worktree-isolated agents from editing the primary checkout — 7/11 execute agents hit the trap in one raid; only a hook guard closes the class (ticket 0318)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 07d7cb00-b790-4546-9c26-062a639b4ad1
---

In the 2026-07-13 ticket-pipeline raid (11 sequential hunt waves), 7 of 11
worktree-isolated execute agents let their first Edit/Write land in the
primary checkout via absolute `~/.claude/...` paths, despite the trap being
documented in `rules/workflow.md` and despite increasingly explicit
"WORKTREE DISCIPLINE" warnings added to each successive agent prompt. All
self-recovered, but each recovery cost tokens and one nearly polluted main.

**Why:** the model resolves file paths from conversation context (ticket
bodies, tool outputs quoting primary paths), not from its git cwd; a prose
warning competes with every quoted absolute path and loses often.

**How to apply:** do not rely on prompt text to keep agent edits inside a
worktree. Until ticket 0318 lands (PreToolUse `Edit|Write` guard denying
primary-checkout writes during worktree sessions, mirroring
`scripts/guard-cd-primary-repo.sh` on the Bash surface), expect the trap in
~2/3 of worktree-isolated agent runs and check `git -C <primary> status`
after each agent returns. Related: [[fork-skills-bare-context]],
[[parallel-execute-branch-contamination]].
