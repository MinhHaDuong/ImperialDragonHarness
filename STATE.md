# Imperial Dragon Harness — State

Last updated: 2026-05-10T10:02Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-10T10:02Z -->

**Tickets:** 18 ready · 5 blocked — `erg ready tickets/` for full list
**Recent commits:**
  31afc7b ticket(0047): close — merged PR #128
  f3f669d ticket(0108): close — merged PR #127
  dc0f9eb feat(0047): add --max-turns caps to beat.py skill invocations (Phase 1) (#128)
  057e296 feat(0108): add SUPERVISOR ACTIONS section to nightbeat-report (#127)
  943711b repair: raise chemin-de-voix budget_housekeeping 0.58→0.70 (error_max_budget_usd x2)

## Blockers

- **0057**: needs git-erg/0039 (`erg log`) + git-erg/0040 (`erg new`) in binary
- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects
- **git-erg/0008**: rewrite branch-as-claim check in `erg ready`

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
