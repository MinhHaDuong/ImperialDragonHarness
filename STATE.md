# Imperial Dragon Harness — State

Last updated: 2026-05-15T09:20Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-15T09:20Z -->

**Tickets:** 1 ready · 4 blocked — `erg ready tickets/` for full list
**Recent commits:**
  b14de73 chore(tickets): fix ID collisions — renumber 0163→0165, drop obsolete 0164 watch-ticket
  f6435b9 docs(skills): regenerate catalog — add dream skill
  32f00e4 chore(state): close 0070, add /dream exercise reminder
  48bfcb6 chore(tickets): trim 0070 exit criteria — drop post-merge timer check and pre-merge dry-run gate
  220c0a1 feat(dream): autonomous nightly memory consolidation (#0070) (#205)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **Exercise /dream**: run `/dream -home-haduong--claude` to validate the skill on real memory data
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Consider: refactor nightbeat risk-review to use check-readiness skill (0152)

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
