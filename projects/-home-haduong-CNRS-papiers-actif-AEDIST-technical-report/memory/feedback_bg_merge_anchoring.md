---
name: bg-merge-anchoring-and-automerge-race
description: "In background sessions, point erg-pr-merge at the PR-branch worktree with `-C <pr-worktree>` (ticket 0344), not a `cd … &&` compound; a bounced run may already have QUEUED auto-merge — check `gh pr view N --json state` before retrying"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 632220ae-86ec-4604-89d6-daf57b6c0466
---

During the 2026-06-12 final-check raid, erg-pr-merge bounced four times across
three PRs; all four were recoverable but cost a round-trip each.

**Why:** (1) In background sessions the shell cwd resets to the session worktree
between Bash calls — and the PR branch usually lives in the *executor agent's*
worktree, so an `erg-pr-merge N` run from the wrong cwd bounces with "must run
from PR branch". (2) The script is not idempotent across retries: a
bounced-looking run may already have pushed the ticket-close commit and QUEUED
auto-merge; the retry then bounces with "mergeability is UNKNOWN" because the PR
is mid-merge or already MERGED.

**How to apply:** point the merge at the PR-branch worktree with `-C`
(ticket 0344), which supersedes the old `cd <pr-worktree> && …` single-compound
anchoring — the bare form matches the standing allow rule from any cwd, where a
`cd` prefix does not. Wrap it in `timeout` per this project's shell-stall rule
([[feedback_shell_timeout_no_loops]]):
`timeout 30 git -C <agent-worktree> fetch origin --quiet && timeout 90 ~/.claude/skills/merge/erg-pr-merge -C <agent-worktree> N`.
Before ANY retry, check `gh pr view N --json state` — if MERGED, verify the
close commit landed (`git log origin/main` shows "ticket(NNNN): close and
archive") instead of re-running. CI-pending bounces are benign: wait and retry
the same `-C` invocation. [[erg-id-collision-across-branches]]
