---
name: feedback-merge-classifier-blocks-autonomous-raid
description: Auto-mode permission classifier denies erg-pr-merge in background raids despite STATE.md standing merge authorization; plan the merge handoff.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 09a6ef97-cfc0-47a6-8a5d-6968b96702ff
---

In a background /raid (2026-06-11, PR #979 / ticket 0537), the auto-mode
classifier denied `erg-pr-merge`, citing the project rule "never close
merge requests without explicit user confirmation" — it does not accept
STATE.md's standing authorization (author 2026-06-11: merge on APPROVED +
green CI) as in-transcript confirmation.

**Why:** the classifier only sees the transcript; durable authorizations
recorded in STATE.md don't count for it. Raid Phase 7 therefore stalls at
the merge step in unattended sessions.

**How to apply:** end the raid with a `needs input:` merge handoff (PR
APPROVED + green CI + exact `/merge N` command), don't retry or work
around the denial. The user can unblock future raids with a Bash
permission rule for `~/.claude/skills/merge/erg-pr-merge` in settings.
Also: after a failed-then-user-completed merge, the killed erg-pr-merge
run may leave the PR-branch worktree with a stale pre-rebase INDEX
(staged diff that re-opens closed tickets / reverts prose) — that staged
state is pre-rebase debris, `git reset --hard HEAD` it before worktree-gc.
See [[feedback-erg-pr-merge-partial-success]].
