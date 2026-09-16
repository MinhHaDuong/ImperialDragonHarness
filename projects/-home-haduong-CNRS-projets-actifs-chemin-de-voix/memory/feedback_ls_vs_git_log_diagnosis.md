---
name: feedback-ls-vs-git-log-diagnosis
description: "When ls doesn't show files that git log says are committed, check git status first — staged reverts can desync working tree from HEAD even when origin is in sync."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 73828333-04df-4434-9a2c-e4eb6149a691
---

When the user reports `ls` doesn't show files that `git log` claims are committed, do not jump to "your checkout is behind origin, do `git pull`." Check `git status --short` first — a parallel session or stale staging can leave the working tree and index divergent from HEAD even when `origin/master == local master`.

**Why:** In this project, a parallel Claude session (commit a981e77 pattern) staged a revert that deleted 0129/0130 and un-archived 0070 in the main checkout. I diagnosed "checkout is behind, git pull will fix it." The user ran `git pull` → "déjà à jour" — because origin already matched local HEAD. The real divergence was working tree ↔ HEAD, not local ↔ origin. Recovery wasted a turn.

**How to apply:** Before suggesting `git pull` when files appear missing on disk:
1. `git status --short` — any `D`, `M`, `R`, or unstaged changes? If yes: the issue is local divergence, not remote lag.
2. Only if status is clean: `git log local..origin` to confirm a remote/local gap.

The pattern "ls and git log disagree" has at least two causes. Diagnose, don't pattern-match the common one.

Related: [[feedback_parallel_agent_id_collision]].
