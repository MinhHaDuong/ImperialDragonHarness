# merge — cases
Updated: 2026-11-10 · authority: current merge skill; cases remain dated observations

## Gated landing refused as "Merge Without Review", PRs 2346-2441 — 2026-11-09/10
Context: gaze REVIEWED and verify-gate APPROVED on notes. What happened: the permission classifier refused `raid_land.py` in interface sessions (2346, 2367, 2378, 2397, 2441), and refused a delegate briefed to retry; the same calls ran once the author typed "Land <PR>". Landings ran unrefused where gaze and gate had run in the same session (2402, 2414, 2428, 2436). A yes given before the PR had a number did not count (2397). Outcome: every PR landed; a "Harness Gated Merge" allow rule was added, with no established effect. Source: memory/journal/2026/2026-11-09-roar-raid-5c2a37-landing-and-doudou-control.md; memory/journal/2026/2026-11-10-roar-pr2397-audit-names-runtimes-read.md; memory/journal/2026/2026-11-10-roar-pr2378-reach-tail-raid-6ee79f.md.
Use: try once; on a refusal, park merge-ready and hand the author `Land <PR>` with the ruled tip; never retry verbatim or delegate the retry.

## Ticket close broke a memory link, PR 2385 — 2026-11-10
Context: ticket-only PR closing 1465 by ruling, bookkeeping tier. What happened: archiving moved the ticket; a memory topic still linked its open path, and the after-merge runner painted main red (1506), since bookkeeping runs no test suite. Reaction: PR 2390 fixed the link. Source: memory/journal/2026/2026-11-10-roar-morning-landings-1369-1417-1465-1504-1505-1506.md.
Use: before landing a close, grep `memory/` and `design/` for the ticket's open path and run `tests/test_memory_v8_pilot.py`.

## Sibling merge voided an APPROVED-bound gate, PR 2402 — 2026-11-10
Context: a sibling PR on the same script landed ten seconds after the gate wrote its record. What happened: the verdict write was refused as stale; no round was spent. Reaction: the executor merged main into the branch (no force-push), a narrow gaze reviewed the merge commit, the gate approved in round 1. Outcome: merged 14 minutes after the refusal. Source: memory/journal/2026/2026-11-10-roar-pr2402-codex-reader-raid-3429da.md.
Use: merge main in rather than rebase; a rebase changes the range and voids the gaze too.

## Ticket filing accidentally close-claimed, PR 2223 — 2026-11-05
Context: a new-ticket PR body used `**Ticket:** … (new; filed, not closed)`. What happened: forge resolve returned claim 1450 despite the parenthetical. Reaction: removed the Ticket line. Outcome: bookkeeping merge filed 1450 and left it open. Source: memory/journal/2026/2026-11-05-pr2223-filing-pr-ticket-line-parsed-as-close-claim.md.
Use: filing-only PRs name the ticket in a Refs line; check the parsed claims before landing.
