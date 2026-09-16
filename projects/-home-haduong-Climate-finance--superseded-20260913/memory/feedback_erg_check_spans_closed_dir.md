---
name: feedback_erg_check_spans_closed_dir
description: "erg check scans tickets/ and tickets/closed/ together, so closing one half of a duplicate ID does not clear the collision"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d6d0d59-8438-4787-abcf-815081fd8fff
  modified: 2026-07-28T07:14:07.686Z
---

`erg check` reports `duplicate ID 'NNNN'` across both directories. Archiving one
of the pair to `tickets/closed/` leaves the violation standing — verified
2026-07-28 on PR #1234's real tree, which held `0371-swap-agent-token…` open and
`0371-included-shared-tables…` closed and still failed.

**Why:** closing a ticket feels like retiring its ID, so a PR that closes one
duplicate reads as the repair. It is not. The only repair is a renumber. A PR
body claiming `erg check tickets/ PASS` is also easy to compute on a base that
predates one of the two files, which is how the stale verdict survived to
review — the same stale-base trap as the cross-PR collision gate.

**How to apply:** after a ticket PR merges, run `erg check tickets/` against a
checkout of `origin/main` (this repo has no CI, so nothing else will). On a
duplicate, decide the interloper by landing order —
`git log --diff-filter=A -1 -- <path>` on each — and renumber the one that
landed second, clear of the frontier per
[[feedback_concurrent_ticket_id_repair]]. Check inbound cross-references first:
the earlier ticket is usually named by other tickets, which is a second reason
it keeps the ID. When the duplicate's file is already touched by someone else's
open PR, report the recipe there rather than renumbering in parallel.
