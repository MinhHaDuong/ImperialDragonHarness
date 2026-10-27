# Raid sitrep ticketed; gated merge landed without a record on the author's instruction (PR 1725, ticket 1246)

Date: 2026-10-27
Project: ImperialDragonHarness

**Context.** From an arena session, the author asked whether raids have a coordinator watchdog: a 1-minute idle nudge and a 15-minute sitrep. A read of `skills/raid/` found only the executor-side breaker (`raid-breaker.py`, 10-minute stall window, `--wait` wake on `STALL`/`GATE_TIMEOUT`). Nothing woke the coordinator on a timer or printed a sitrep. The session set aside the 1-minute nudge on cost (each wake re-reads the full context, about 9M cached tokens/hour at 150K context, a derived estimate) and recommended a 15-minute sitrep with the nudge folded in.

**Decision.** The author asked for the sitrep as a portable ticket. Ticket 1246 splits a runtime-agnostic producer (`scripts/raid-sitrep.py`, reading durable state only) from a per-runtime wake source behind `<!-- harness-extension-point -->`. Where a runtime has no wake source, it degrades to wave-boundary sitreps. The raid log gets a fixed path.

**Merge path.** PR 1725 added only the ticket file (bookkeeping tier, gated base). Gate record 1 passed on candidate 71b868c1 (2410 passed, 4 skipped, 76.5 s), but PR 1726 merged meanwhile and the check asked for 329db22b. Gate record 2 passed on 329db22b; PR 1722 merged meanwhile and the check asked for d480f63c. Following the recipe (a check that still answers 2 after one re-record goes in the report, not into a loop), the session stopped and reported. The author then said "Just merge, dont rerun the tests". The session merged with `--match-head-commit 3e85dbcf` and no record on the final candidate. The read-back answered `MERGED 3e85dbcf -`. The PR comment records the duration and the bypass.

**Outcome.** Ticket 1246 open on main. No code changed.
