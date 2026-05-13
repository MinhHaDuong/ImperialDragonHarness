# Imperial Dragon Harness — State

Last updated: 2026-05-13T19:35Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-13T19:35Z -->

**Tickets:** 2 ready · 8 blocked — `erg ready tickets/` for full list
**Morning review:** `/nightbeat-report` (narrative) · `/nightbeat-risk-review` (interactive triage before next run)
**Recent commits:**
  f034ae8 ticket(0103): close and archive — PR #189
  078f748 refactor(beat): replace threading with asyncio for subprocess management (#0103) (#189)
  a994e2c ticket(0131): close and archive — PR #188
  2d5b722 refactor(skills): compact verify-gate and verify skill files (#0131) (#188)
  b6bb88a ticket(0150): close and archive — PR #187

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- **0070**: /dream skill — research gate cleared (docs/dream-research.md); ready to implement
- **0154**: add pytest to CI pipeline (surfaced in raid PR #189)
- **0142**: verify agents must not use main repo as workspace
- **0141**: subprocess timeout gaps in git_utils, project-state, refresh-STATE
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
