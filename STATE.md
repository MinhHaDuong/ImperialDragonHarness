# Imperial Dragon Harness — State

Last updated: 2026-05-11T21:13Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-11T21:13Z -->

**Tickets:** 24 ready · 7 blocked — `erg ready tickets/` for full list
**Recent commits:**
  9501354 ticket(0125): open — housekeeping should delete stale branches for closed tickets
  9d90dcd chore: update erg binary to b6168d1, unblock 0044, migrate Tags:→Tag:, archive 0115
  9784205 chore: close 0102 + 0106 (PRs merged), archive both
  95b12e9 chore: add git-erg to beat rotation
  521bc45 ticket(0124): open — fix leak-guard violation on main (skills/raid/SKILL.md)

## Blockers

- **0057**: needs git-erg/0039 (`erg log`) + git-erg/0040 (`erg new`) in binary
- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **Review & merge open PRs**: #142 (0051 fallback rotation), #141 (0117 Tag rename), #136 (0113 denial catalog), #143 (0124 leak-guard)
- **0125**: housekeeping should delete stale branches for closed tickets
- **git-erg/0130**: erg tag/untag CLI — prerequisite for replacing branch-as-claim
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
