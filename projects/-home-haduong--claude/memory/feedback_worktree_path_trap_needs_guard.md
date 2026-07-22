---
name: worktree-path-trap-needs-guard
description: Prompt warnings do not prevent worktree-isolated agents from editing the primary checkout — 7/11 execute agents hit the trap in one raid; the 0318 hook guard (merged PR #562) now denies the class
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
worktree. RESOLVED 2026-07-13: ticket 0318 (PR #562) hardened
`scripts/pretooluse-worktree-path-guard.sh` from advisory to deny (exit 2)
on `Write|Edit|NotebookEdit` — primary-checkout writes during worktree
sessions are now blocked, with a narrow `projects/*/memory/*` exemption and
a human-only `GUARD_ALLOW_PRIMARY_EDIT` escape hatch. The post-agent
`git -C <primary> status` spot-check is now a fallback, not standing.
Residual gaps (realpath/symlink evasion, escape-hatch env provenance) are
ticketed as 0323. Related: [[fork-skills-bare-context]],
[[parallel-execute-branch-contamination]].
