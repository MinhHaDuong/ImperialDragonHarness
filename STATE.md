# Imperial Dragon Harness — State

Last updated: 2026-05-14T20:12Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-14T20:12Z -->

**Tickets:** 7 open · 0 ready — `erg ready tickets/` for full list
**Test suite:** 223 passing · CI all green
**Recent commits:**
  1647cfd chore(tickets): close and archive 0160, 0161, 0162 after merge
  eac6214 docs(skills): auto-generate catalog in README.md (#201)
  f2c569d feat(beat): async streaming in run_skill (#204)
  c62cd31 fix(beat): lazy-load PROJECTS to unblock pytest-guard (#203)
  c13f1b4 chore(tickets): archive 5 closed tickets (re-do after rebase)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **0070**: /dream skill — research gate cleared (docs/dream-research.md); ready to implement
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Consider: refactor nightbeat risk-review to use check-readiness skill (0152)

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
