# Imperial Dragon Harness — State

Last updated: 2026-05-09T16:45Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status

**Tickets:** 29 open — `erg ready tickets/` for full list
**Recent commits:**
  4d78892 ticket(0105): close — done
  550897f fix(0105): survey script — journal watermark + gh pr list PR discovery (#120)
  878c17d fix(beat): housekeeping budget +20% + ticket 0106 for raid timeout (#119)
  c1b482c feat(0105): supervisor systemd units + survey script + permissions (#118)
  d216953 feat: nightbeat supervisor skill (ticket 0105) (#116)

**Nightbeat supervisor** (`claude-nightbeat-supervisor.timer`) live on padme. Fires every 15 min during nightbeat window. Survey script uses journal watermark + forge API for PR discovery. Housekeeping budget raised to $0.48 for both projects.

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
