---
name: project_zoteus_fork_git_isolation
description: zoteus-fts5's code lives in a nested independent repo under fork/, which the worktree guard blanket-blocks from git
metadata:
  type: project
---

`zoteus-fts5` holds tickets, STATE and `bench/`; the actual TypeScript lives in
`fork/`, a checkout of `MinhHaDuong/zoteus` that is a **separate git repository**
and git-ignored by the outer one.

Claude Code's own worktree-isolation guard on the Bash tool blanket-refuses
every `git` command under the primary checkout path once a session has entered
a worktree — including read-only `git status` — because it treats any path
beneath the primary root as "the shared checkout". It does not know `fork/` is
its own repo. The user's `guard-cd-primary-repo.sh` is *not* the one firing; it
only matches `cd <primary-root>` exactly.

Observed 2026-08-21: file writes and `npx vitest` in `fork/` work fine; only
`git` is blocked. `ExitWorktree` cleared it (in that session it reported "no
active EnterWorktree session", and the guard stopped firing thereafter).

**How to apply:** plan fork work as edit-and-test under isolation, then do the
git work after leaving the worktree. Executor subagents cannot commit there
either — tell them explicitly never to run git, and do the commit yourself
afterwards. Storage-layer work landed on the fork branch `fts5-storage`, off
`fts5-base`; note `fts5-base` tracks `origin/index-max-items-runtime`, the
branch backing open upstream PR #11, so a bare `git push` from it would
contaminate that PR.
