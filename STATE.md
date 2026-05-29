# Imperial Dragon Harness — State

Last updated: 2026-05-29T13:25Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-29T13:25Z -->

**Tickets:** 6 ready · 6 blocked — `erg ready tickets/` for full list
**Recent commits:**
  0a40ddf docs: regenerate skills catalog after squash-merge rename
  baf2914 tickets: file 0178 — housekeeping detect and fix ticket corpus errors
  0460305 config: auto mode, drop explicit model/effortLevel, skipAutoPermissionPrompt
  081cce4 chore: squash-merge is disabled — purge stale wording across harness
  7fecc71 Merge remote-tracking branch 'origin/main'

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
