# Imperial Dragon Harness — State

Last updated: 2026-05-15T20:05Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-15T20:05Z -->

**Tickets:** 0 ready · 5 deferred/blocked — `erg ready tickets/` for full list
**Recent commits:**
  9e2d136 chore(nightbeat): remove IDH from beat roll
  984303b chore: tag 0165 deferred, wire make check target
  f94978c fix(probe): filter erg ready --json by ready:true field
  c6cb68f dream: consolidate chemin-de-voix memory (26→26 entries)
  dc46bcb chore(state): refresh 2026-05-15 end-of-session — dream merged, 233 tests

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **Exercise /dream**: run `/dream -home-haduong--claude` to validate the skill on real memory data
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Consider: refactor nightbeat risk-review to use check-readiness skill (0152)
- Nightbeat suspended (no projects in roll); re-enable when new project added

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
