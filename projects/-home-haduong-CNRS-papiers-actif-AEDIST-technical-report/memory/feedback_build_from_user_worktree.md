---
name: feedback-build-from-user-worktree
description: "When the user edits files in the main working tree while you work in an isolated worktree, the same file diverges — build from their source and verify before syncing"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d93d059e-0241-40fb-b77c-497429967a47
---

During the slides-en.tex work, the user was editing `slides/slides-en.tex`
directly in the **main** working tree (uncommitted) while I made a separate
change (a figure crop) in an **isolated worktree** that I pushed via PR to
origin/main. Result: the same file diverged — the crop landed on origin, the
user's rewording stayed local-only — and when they said "make slides-en.pdf"
I built the worktree (crop-only) version and copied it over their PDF,
showing them the wrong thing.

**Why:** worktree isolation means my edits and the user's main-tree edits are
two independent copies of the same file. PDFs are gitignored, so a build can
silently render whichever copy I point `make` at.

**How to apply:**
- When the user asks to build/render/show a manuscript or deck **they are
  actively editing**, build from THEIR working tree (the main repo path),
  not from the worktree copy. Their uncommitted edits are the source of truth.
- Before `git checkout -- <file>` to sync/fast-forward local main, confirm the
  working-tree file is byte-identical to what's on origin (`diff -q` against
  `git show origin/main:<file>`). Discard only when captured. Never clobber
  divergent uncommitted user edits.
- To merge a user's local-only edits with a change already on origin, ask for
  the resolution ("yours/mine per region"), then fold the small change into
  THEIR file (different frames/sections merge clean), commit on a branch off
  origin/main, PR, merge, then sync. Related: [[feedback_worktree_not_stash]],
  [[feedback_rtk_git_log_stale]].
