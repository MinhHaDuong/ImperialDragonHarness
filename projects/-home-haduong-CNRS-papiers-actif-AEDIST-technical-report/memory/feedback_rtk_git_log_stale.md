---
name: feedback-rtk-git-log-stale
description: "rtk-filtered `git log` can omit/lag merge commits; use `rtk proxy git` for ground truth on git state"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d93d059e-0241-40fb-b77c-497429967a47
---

The rtk proxy filters `git log` output and can hide or lag merge commits.
After merging PR #619 with `gh pr merge --merge`, the rtk-filtered
`git log --oneline origin/main` kept showing the pre-merge tip (7fba116)
as HEAD, omitting the GitHub merge commit (3b4fc62). Meanwhile
`git rev-parse HEAD` returned the real merge commit. This nearly caused
wrong reasoning about which commit a new branch was based on.

**Why:** rtk strips/caches commits to save tokens; merge commits are a
casualty. The filtered log is not a faithful view of history.

**How to apply:** When git *state* matters (verifying a branch base, a
merge landed, HEAD, ancestry) — not just browsing — get ground truth with
`rtk proxy git log ...` / `rtk proxy git rev-parse ...` / `rtk proxy git status`.
Cross-check `rev-parse HEAD` against `log` top; if they disagree, trust the
raw proxy output. Related: [[feedback_gh_merge_worktree]].

**Scripting corollary (2026-06-11):** rtk also rewrites *empty* output into
an "ok" summary line, so `git status --porcelain | grep -q .` reads a CLEAN
tree as dirty, and `git branch` current-branch markers land on the wrong
line. Any script that PARSES git output (dirty checks, branch loops,
`wc -l` counts) must call `rtk proxy git ...` explicitly — plain git inside
a Bash tool call goes through the hook rewrite even mid-pipeline.
