# PR 2223: a ticket-filing PR's `**Ticket:**` line parsed as a close claim

Date: 2026-11-05 · Project: ImperialDragonHarness · PR #2223 (ticket 1450)

## Context

The author asked for a new ticket (1450, no-forge backend cannot list open
review requests). It was filed on branch explore-noforge-list-2531941-5216 and
opened as PR #2223 to land it on main, leaving it open.

## Events

- The first PR body began `**Ticket:** tickets/1450-....erg (new; filed, not closed)`.
- Before merging, `forge.py resolve 2223` reported `claims: ['1450']`: the
  parenthetical did not stop the line from being a close claim, so the merge
  recipe's step 1 would have closed and archived the ticket the PR was filing.
- The body was edited with `gh pr edit` to name the ticket without a
  `**Ticket:**` line; `resolve` then reported `claims: []`.
- Landed with `raid_land.py 2223 --ruled-head - --ruled-claims - --cleanup`
  (tier bookkeeping, gated base). Read-back: `MERGED f173c977… -`; main at 475e5e17.
- Attribution: `not derivable: review (none on notes)`, expected for an
  ungazed bookkeeping PR.

## Outcome

Ticket 1450 is on main and open. No ticket was closed by mistake.
