# Imperial Dragon Harness — State

Last updated: 2026-05-13T05:48Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-13T05:48Z -->

**Tickets:** 20 ready · 4 blocked — `erg ready tickets/` for full list
**Morning review:** `/nightbeat-report` (narrative) · `/nightbeat-risk-review` (interactive triage before next run)
**Recent commits:**
  4872f22 chore: housekeeping timestamp 2026-05-13T05:48Z
  e2127ee chore: ticket 0142 — verify agents must not use main repo as workspace
  cb43849 chore: ticket 0141 — subprocess timeout gaps in git_utils/project-state/refresh-STATE
  98917ce ticket(0140): close — moot, Blocks: header removed from spec
  cb589b2 feat(0125): housekeeping deletes stale branches for closed tickets (#162)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **0142**: verify agents must not use main repo as workspace (rogue checkout problem)
- **0141**: subprocess timeout gaps in git_utils, project-state, refresh-STATE
- **audit-rename-agnostic-guard**: 6-commit branch needs PR + verify before merge
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
