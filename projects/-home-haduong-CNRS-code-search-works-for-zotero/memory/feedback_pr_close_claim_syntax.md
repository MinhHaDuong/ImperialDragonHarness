---
name: pr-close-claim-syntax
description: erg-pr-merge only executes a close claim written as "Ticket: tickets/NNNN-slug.erg" on its own line; "**Ticket:** NNNN" and title prefixes are not claims and the merge bounces.
metadata:
  type: feedback
---

Write the PR body's close claim exactly as `Ticket: tickets/NNNN-<slug>.erg`
(or `Ticket-ref: …` / `Ticket: none`), first line, no markdown bold.

**Why:** on 2026-09-22 PR #607's body carried `**Ticket:** 0810` and
`erg-pr-merge` refused with "no close-claim in PR body". The fix was a body
PATCH via the API recipe (`gh pr edit` is broken here, see
[[gh-pr-edit-broken-use-api-patch]]); had the PR been merged by any other
route the ticket would have stayed open silently — the DROPPED class
`check-close-claims.sh` exists for.

**How to apply:** when briefing an execute/finisher agent that opens the PR,
give the literal line, not "add a Ticket line".
