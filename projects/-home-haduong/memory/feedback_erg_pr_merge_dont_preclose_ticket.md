---
name: feedback_erg_pr_merge_dont_preclose_ticket
description: "Don't manually erg-close/archive a ticket before opening its PR — erg-pr-merge does that itself and its Ticket: line regex only recognizes a flat tickets/NNNN-slug.erg path"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 205d21b8-033a-430e-bad8-23da7bf7a8f0
  modified: 2026-09-15T15:11:57.922Z
---

`erg-pr-merge`'s close-claim regex (`^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+`)
requires "tickets/" to be followed immediately by digits — it does not match
`tickets/closed/NNNN-slug.erg`. The script's own design (its header comment:
"erg close NNNN ... + git add + commit + push (always)") is to run `erg close`
+ `erg archive` itself, as part of the merge, on a ticket that is still open
and still living at the flat `tickets/NNNN-slug.erg` path when the PR is
opened.

**Why:** twice in one cadens session (2026-09-15, tickets 0038 and 0040), the
ticket was manually closed and moved to `tickets/closed/` before the PR body
was written. `Ticket: tickets/closed/NNNN-slug.erg` then fails the regex
entirely ("no close-claim in PR body"), and `Ticket: tickets/NNNN-slug.erg`
(flat, matching the regex) then fails the later cross-check because the file
genuinely isn't at that path anymore ("close-claimed ticket(s) NNNN are
absent from tickets/ at the branch tip"). The workaround both times was
`Ticket-ref: tickets/NNNN-slug.erg` (flat path; Ticket-ref is never
cross-checked against the filesystem) — correct in effect since the ticket
was already closed, but a workaround, not the intended flow.

**How to apply:** in any project using `erg-pr-merge`, leave the ticket open
(don't `erg close`/`git mv` it into `closed/` yourself) when opening the PR;
put `Ticket: tickets/NNNN-slug.erg` (flat path) in the PR body and let the
merge script close and archive it. Reserve manual `erg close` + move for
tickets that must appear closed in the diff for review purposes, and use
`Ticket-ref: tickets/NNNN-slug.erg` (flat form, regardless of the ticket's
real path) to bypass the close-claim guard in that case. Worth fixing at the
source too — the regex could accept an optional `closed/` segment — but that
edit lives in the `erg-pr-merge` script/repo itself, not in a project that
merely uses it.
