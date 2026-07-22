---
name: feedback-background-session-manuscript-pr-workflow
description: "Background sessions force worktree+PR isolation even for manuscript prose (normally co-edited in place); primary checkout's stale uncommitted diff must be reconciled after merge, not just fetched"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8be8f7a-2eb1-4c58-ba7b-8c8397fc6d6c
---

The project's own git rule says manuscript prose is co-edited in place in
the author's primary checkout, no worktree/PR needed. But a **background
job** session's harness-level isolation guard fires regardless of that
project convention — the first Edit/Write attempt on
`deliverables/manuscript/manuscript.qmd` in a background session was
rejected until `EnterWorktree` ran, and the background-session system
prompt separately instructs committing, pushing, and opening a PR rather
than editing in place.

**Why it matters**: the primary checkout already had uncommitted prose
edits (from an earlier *interactive* session, before this became a
background job) when the guard fired. Those changes weren't in the new
worktree — `EnterWorktree` branches from a clean ref, it does not carry
over another worktree's dirty state. Had to `cp` the primary checkout's
modified files into the new worktree by hand before continuing edits
there, then after merging the PR, reconcile the primary checkout: back up
its now-stale uncommitted diff, `git checkout --` to discard it, then
`git merge --ff-only origin/main` — a plain `git merge --ff-only` fails
outright with local modifications present, so the discard has to happen
first (safely, since the diff was fully superseded by what actually
merged).

**How to apply**: when a background-job session needs to edit a
prose-in-place file and the primary checkout already has uncommitted
changes to that file, `cp` those changes into the fresh worktree before
continuing — don't silently drop them. After merging back, always diff
the primary checkout's dirty copy against `origin/main`'s content before
discarding it (`git checkout --`) to confirm it's genuinely superseded,
not unique unmerged work; back it up to the job's tmp dir regardless.
