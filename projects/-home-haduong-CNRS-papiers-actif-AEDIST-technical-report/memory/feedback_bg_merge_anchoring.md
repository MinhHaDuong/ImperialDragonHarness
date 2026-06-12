---
name: bg-merge-anchoring-and-automerge-race
description: "In background sessions, erg-pr-merge needs `cd <pr-worktree> && …` in ONE compound (cwd resets between Bash calls); a bounced run may already have QUEUED auto-merge — check `gh pr view N --json state` before retrying"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 632220ae-86ec-4604-89d6-daf57b6c0466
---

During the 2026-06-12 final-check raid, erg-pr-merge bounced four times across
three PRs; all four were recoverable but cost a round-trip each.

**Why:** (1) In background sessions the shell cwd resets to the session worktree
between Bash calls — and the PR branch usually lives in the *executor agent's*
worktree, so an unanchored `erg-pr-merge N` bounces with "must run from PR
branch". (2) The script is not idempotent across retries: a bounced-looking run
may already have pushed the ticket-close commit and QUEUED auto-merge; the retry
then bounces with "mergeability is UNKNOWN" because the PR is mid-merge or
already MERGED.

**How to apply:** run the merge as one compound anchored in the worktree that
has the PR branch checked out:
`cd <agent-worktree> && gh pr checks N --watch >/dev/null 2>&1; git fetch origin --quiet && ~/.claude/skills/merge/erg-pr-merge N`.
Before ANY retry, check `gh pr view N --json state` — if MERGED, verify the
close commit landed (`git log origin/main` shows "ticket(NNNN): close and
archive") instead of re-running. CI-pending bounces are benign: wait and retry
the same anchored compound. [[erg-id-collision-across-branches]]
