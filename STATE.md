# Imperial Dragon Harness — State

Last updated: 2026-05-14T07:45Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-14T07:45Z -->

**Tickets:** 8 ready · 12 open — `erg ready tickets/` for full list
**Morning review:** `/nightbeat-report` (narrative) · `/check-readiness --mode=nightbeat-history` (interactive triage before next run) or `/check-readiness` (full multi-project audit)
**Recent commits:**
  f58a7dc chore(tickets): fold asyncio into 0158; annotate closed 0103
  c1920fd ticket(0158): beat-log event model — replace state encoding with events
  1abd848 ticket(0157): test suite writes to production beat-outcomes.jsonl
  b6831a3 fix(nightbeat): supervisor timer hourly at H+30 (#193)
  2fc8c65 fix(tickets): sanitize hardcoded home path in 0070 — agnostic-guard violation

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host
- **Layer 2 skip**: `_pick_needed` in `_raid` uses current beat's `in_progress` timestamp as watermark — always finds no commits since NOW → skips pick-ticket every run. Root cause in `read_last_beat_record` call placement. Fix: ticket 0158.

## Next actions

- **0158**: beat-log event model (fixes Layer 2 skip + asyncio streaming) — highest priority
- **0157**: test suite pollutes production beat-outcomes.jsonl — isolate log path
- **0155**: remove stale `_BUILTIN_PROJECTS` fallback in beat.py
- **0154**: add pytest to CI pipeline
- **0151**: extract harness rules into machine-readable format
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- **0070**: /dream skill — research gate cleared (docs/dream-research.md); ready to implement

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
