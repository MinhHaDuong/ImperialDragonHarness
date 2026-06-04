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

Merge is queued via auto-merge; it lands when required checks pass (falls back to watch-then-merge where auto-merge is disabled).
