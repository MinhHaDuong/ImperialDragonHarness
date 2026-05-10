# Imperial Dragon Harness — State

Last updated: 2026-05-11T00:00Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-11T00:00Z -->

**Tickets:** 26 ready · 2 blocked — `erg ready tickets/` for full list
**Recent commits:**
  chore: archive closed tickets 0047, 0064, 0100, 0101, 0108, 0109, 0110
  chore: archive closed tickets 0098, 0099, 0111, 0112
  ticket(0115): per-project max_turns_pick_ticket — supervisor root-cause
  feat(0113): beat denial catalog May 7-10 + ticket 0114 (locked worktrees) (#129)
  feat(0102): migrate beat budgets from projects.json to per-project .claude/beat.json (#125)

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
