# Imperial Dragon Harness — State

Last updated: 2026-05-09T11:18Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-09T11:18Z -->

**Tickets:** 23 ready · 5 blocked — `erg ready tickets/` for full list
**Recent commits:**
  70cc52a fix(state): reroll PR115 — five issues corrected (#117)
  2d9e333 Revert "feat(state): replace-policy rule + refresh-STATE.py script (#115)"
  272e12a feat(state): replace-policy rule + refresh-STATE.py script (#115)
  ea943e3 ticket 0104: block on 0103 (asyncio refactor must land first)
  8085c3e ticket 0104: replace beat.py pipeline orchestration with Prefect 3.x

## Incident — 2026-05-08 night (resolved)

Nightbeat timer stopped after two housekeeping budget failures. Recovery complete: 10 misplaced closed tickets moved to `tickets/closed/`, `erg check` clean.
**Timer still stopped.** Restart: `systemctl --user start claude-nightbeat.timer`

## Blockers

- **0057**: needs git-erg/0039 (`erg log`) + git-erg/0040 (`erg new`) in binary
- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **Restart nightbeat timer** after confirming erg check is clean
- **PR #116** (nightbeat supervisor skill): review and merge
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects
- **git-erg/0008**: rewrite branch-as-claim check in `erg ready`

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
