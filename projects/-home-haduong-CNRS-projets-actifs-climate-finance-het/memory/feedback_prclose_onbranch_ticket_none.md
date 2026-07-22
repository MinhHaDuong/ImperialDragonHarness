---
name: feedback_prclose_onbranch_ticket_none
description: "If you close+archive a ticket on-branch (hunt already-done path), the PR body must say `Ticket: none`, not `**Ticket:** tickets/closed/NNNN` — erg-pr-merge rejects the archived path and would double-close"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3f035edb-1270-4e9c-b00d-7d4c1c76882f
---

When a ticket is closed AND archived on the branch *before* the PR merges (the
hunt already-done flow, or any pre-merge close per [[feedback_erg_close_archive]]),
the ticket file has already moved to `tickets/closed/NNNN-...`. Two things then
break the normal `**Ticket:** tickets/NNNN` close-claim convention:

1. **Regex mismatch.** `erg-pr-merge` parses close claims with
   `^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+` — it expects digits *immediately*
   after `tickets/`. A `tickets/closed/0236-...` path does not match, so the
   script reports "no close-claim in PR body" and aborts (`set -e`).
2. **Double-close trap.** Even if the regex matched, `erg-pr-merge` would run
   `erg close` again on an already-archived ticket → "no ticket found" (the
   non-idempotent trap from `rules/git.md`).

**How to apply:** if the branch already carries the close+archive commit, put
`Ticket: none` in the PR body (with a prose note that ticket NNNN is closed
in-branch, commit SHA). Do NOT use `**Ticket:** tickets/closed/...`. Cost of
getting it wrong: burned two merge retries on PR #1000 (2026-07-10) — first the
draft state, then this close-claim mismatch.

**Alternative (cleaner for next time):** leave the ticket *open* on-branch and
let `erg-pr-merge` close+archive it at merge via a normal `**Ticket:**
tickets/NNNN` line — the tool is built to do exactly that. Pre-closing on-branch
only makes sense for the hunt already-done path where no PR-side close is wanted.
