# merge — cases
Updated: 2026-11-08 · authority: current merge skill; cases remain dated observations

## Ticket filing accidentally close-claimed, PR 2223 — 2026-11-05
Context: a new-ticket PR body used `**Ticket:** … (new; filed, not closed)`. What happened: forge resolve returned claim 1450 despite the parenthetical. Reaction: removed the Ticket line; resolve then returned no claims. Outcome: bookkeeping merge filed 1450 and left it open. Source: memory/journal/2026/2026-11-05-pr2223-filing-pr-ticket-line-parsed-as-close-claim.md.
Use: filing-only PRs name the ticket in a Refs line; check the parsed claims before landing.

## Stale gate records, PR 1725 — 2026-10-27
Context: ticket-only PR 1725, gate record on a busy main. What happened: two records went stale as PRs 1726 and 1722 merged meanwhile. Reaction: stopped after one re-record and reported, as the recipe says; the author answered "Just merge, dont rerun the tests", and the merge used `--match-head-commit`. Outcome: MERGED, bypass noted on the PR. Source: memory/journal/2026/2026-10-27-raid-sitrep-ticket-1246.md; memory/topics/user-rulings.md.
Use: record, merge, retry once, then report; an author waiver covers that PR only.

## Hand close dropped a ticket, PR 1924 — 2026-10-28
Context: PR 1924 for ticket 1316, closed by hand. What happened: `erg close` already moved the file, so `git add -u tickets/` staged only the deletion; the pushed commit dropped the ticket and `erg check` passed. Reaction: amended, force-pushed with lease before the gate. Outcome: no ticket lost. Source: memory/journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md.
Use: land through `scripts/raid_land.py`, which stages both sides; after any hand close, read `git show --stat HEAD`.

## Gate record push, PRs 2033 and 2035 — 2026-10-30
Context: the gate record reached local `refs/notes/gate` but not origin's. What happened: another process rewound the local ref, so a push by ref name exited 0 and sent nothing (ticket 1366). Reaction: PR 2033 pushed by commit id with an `ls-remote` read-back; PR 2035 kept the commit-id push and dropped the read-back. Outcome: the author ruled 2026-11-01 (ticket 1373) that the exit code answers for a commit-id push; the exception stays in memory, `rules/git.md` unchanged. Source: memory/journal/2026/2026-10-30-push-by-commit-id-exit-code-1366.md.
Use: add no read-back to a push by commit id (`scripts/merge-gate.py`); a push by ref name still needs one.
