---
name: cross-session-worktree-hijack
description: "Finished agent worktrees can be re-pointed to another session's branch — verify `git branch --show-current` before running rebase/merge from one"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: df33291b-b7e0-4267-8f65-a75c859e7ac1
---

A finished background-agent worktree is not yours just because your agent made it. With two sessions raiding the same repo (2026-06-04), the parallel session's close-flow switched MY finished 0228 agent's worktree onto ITS branch (`t0236-close`); my scripted `cd <worktree> && git rebase && push --force-with-lease` then rebased and force-pushed the wrong branch (benign only by luck — the rebase was a no-op).

**Why:** worktrees are shared mutable state across sessions; branch checkout inside them can change between your agent finishing and your merge step running.

**How to apply:** before any mutating git command in a previously-used worktree, assert the branch: `[ "$(git branch --show-current)" = tNNNN ] || stop`. Better: run merges from your own session worktree with `git switch <branch>`, not from finished agent worktrees. Related: [[one-worktree-per-ticket]].
