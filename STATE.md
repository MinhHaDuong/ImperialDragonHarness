# Imperial Dragon Harness — State

Last updated: 2026-05-12T14:30Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-12T14:30Z -->

**Tickets:** `erg ready tickets/` for full list
**Recent commits:**
  88fb9bd chore: update erg binary to fb1aab2 — fix AGENTS.md template (status verb + Tags→Tag)
  ab78bf4 chore: drop merged PRs from next actions, promote git-erg rebuild
  494a1af feat: offload housekeeping git phase to shell script (#34) (#149)
  bd4b9f6 chore: archive closed tickets, migrate Tags→Tag
  b74677e feat: route all .erg mutations through erg binary (#57)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **erg update in consumer projects**: IDH binary rebuilt (fb1aab2) — propagate to chemin-de-voix and any other projects (`erg update` in each)
- **0125**: housekeeping should delete stale branches for closed tickets
- **git-erg/0130**: erg tag/untag CLI — prerequisite for replacing branch-as-claim
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
