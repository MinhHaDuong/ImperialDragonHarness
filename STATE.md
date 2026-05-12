# Imperial Dragon Harness — State

Last updated: 2026-05-12T14:30Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-12T14:30Z -->

**Tickets:** `erg ready tickets/` for full list
**Recent commits:**
  494a1af feat: offload housekeeping git phase to shell script (#34) (#149)
  bd4b9f6 chore: archive closed tickets, migrate Tags→Tag
  b74677e feat: route all .erg mutations through erg binary (#57)
  0b4ba6a feat: restore Five-Claws phase announcement at session start (#54)
  8a94013 ticket: close 0052 — erg edit permissions stable for 13+ days

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **git-erg**: rebuild binary after AGENTS.md template hotfix (`make build` on git-erg, then `erg update` in all projects)
- **0125**: housekeeping should delete stale branches for closed tickets
- **git-erg/0130**: erg tag/untag CLI — prerequisite for replacing branch-as-claim
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
