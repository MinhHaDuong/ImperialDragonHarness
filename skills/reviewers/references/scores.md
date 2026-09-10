# `/reviewers scores [seat-or-candidate]`

Read back the trial cards (`scorecard` lines and `audition` blocks) that the
`scorecard` and `audition` subcommands append to trial tickets, as one sortable
comparison table.
The read surface for 0205's integration review ("trial scorecards reviewed;
promote/drop decided"): comparing candidates no longer means opening ticket
files and eyeballing log lines.

The search is **corpus-wide** and **read-only**: it greps every trial ticket's
log section under `tickets/`, recursing into `tickets/closed/`, so a retired
seat's archived cards are still read. It never edits a roster or writes an
`erg log` line. (This corpus-wide reach is `scores`-only: `scorecard` *writes*
via `erg log <ID>`, which resolves IDs among *open* tickets only — logging a new
card to an archived trial ticket fails "no ticket found". `scores` reads by
grep, so it is not bound by that.)

```
KIND      NAME                 MR/BOARD                   VERIF  CONS  FIND  DUP  UVER  UHAL  OVERLAP   LATENCY      P95     COST  FLAG
audition  hy3-free             10MR                           -     -    59   23     0    36      38%      9.4s    41.0s      n/a  SLOW
scorecard copilot              ImperialDragonHarness#537      0     0     -    -     -     -        -     48.7s        -        -     -
```

No argument → all seats and candidates. An argument filters to one seat or
candidate name. A malformed trial line WARNs on stderr, never silently dropped
(the harvest convention). Only each ticket's `--- log ---` section is read, so
a card quoted in a ticket body as documentation is never mistaken for a result.
`scorecard`'s per-MR columns (`VERIF`/`CONS`) and `audition`'s per-board columns
(`FIND`/`DUP`/`UVER`/`UHAL`/`OVERLAP`) share one table; a `-` marks a column that
does not apply to that row. `LATENCY` shows a candidate's `latency-p50` (the
gate-relevant stat, falling back to the running-sum `latency=` for older cards)
and a seat's per-MR latency; `P95` is the candidate's tail latency; `FLAG`
surfaces the peer-relative `SLOW` verdict (ticket 0353).
