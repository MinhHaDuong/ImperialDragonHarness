---
name: merge
description: Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI).
user-invocable: true
argument-hint: [pr-number]
---

# Merge $ARGUMENTS

Run:
```bash
~/.claude/skills/merge/erg-pr-merge $ARGUMENTS
```

**Cross-repo prerequisite**: the caller must ensure cwd is the target
project and the PR branch is checked out before invoking `/merge`. For
cross-repo flows, this means `cd <project-path> && git fetch origin`
and checking out the PR branch before the call. The script itself is
cwd-based — it never takes a repo or path argument.

## Ticket lines in the PR body

The script reads close intent from the PR **body** only — never the title:

- `**Ticket:** tickets/NNNN-...` (bold or bare `Ticket:`) — a **close claim**:
  the named ticket is closed and archived on merge.
- `Ticket-ref: tickets/NNNN-...` — references a ticket **without closing it**
  (for annotating a deliberately-open ticket).
- `Ticket: none` — the PR closes nothing.
- With none of these lines and a `tickets/` dir present, the script errors.
- Title prefixes like `chore(0216):` are subject references — they **never**
  close anything.

Report stdout/stderr verbatim. If the script exits non-zero, stop and show the error.

A killed or failed `erg-pr-merge` run (non-zero exit after its rebase) can
leave the PR-branch worktree with a stale pre-rebase index: staged diffs that
appear to re-open closed tickets and revert prose. That is not WIP — run
`git reset --hard HEAD` in that worktree before any salvage or gc decision
(ticket 0249 incident, aedist PR #979).

Merge is queued via auto-merge; it lands when required checks pass (falls back to watch-then-merge where auto-merge is disabled). A **draft** PR (roar/raid sweeps file bootstrap PRs as draft) is marked ready automatically before merging — invoking `/merge` is explicit intent to merge.

## After the merge lands

The script itself polls for the merge to land and then runs
`~/.claude/scripts/sync-local-main.sh` on the base branch (rules/git.md
§ Local main syncs eagerly) — no manual sync step. Two outputs still need
action:

- "Merge queued but not yet landed" — the bounded poll ran out (slow CI).
  Confirm the PR reaches MERGED, then run `~/.claude/scripts/sync-local-main.sh`.
- "left untouched" in the sync report — dirty overlap or divergence where the
  base branch is checked out; report it to the caller rather than forcing.

Do not substitute a hand-rolled `merge --ff-only` on the primary checkout:
that advances whatever branch is checked out there.
