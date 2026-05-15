# Imperial Dragon Harness — State

Last updated: 2026-05-14T20:49Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-14T20:49Z -->

**Tickets:** 0 ready · 5 blocked — `erg ready tickets/` for full list
**Recent commits:**
  ed7cb7a chore(tickets): close and archive 0152, 0153
  33c2580 chore(state): refresh after raid 160 161 162 — all merged, 223 tests passing
  1647cfd chore(tickets): close and archive 0160, 0161, 0162 after merge
  eac6214 docs(skills): auto-generate catalog in README.md (#201)
  f2c569d feat(beat): async streaming in run_skill (#204)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **Exercise /dream**: run `/dream -home-haduong--claude` to validate the skill on real memory data
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects
- Consider: refactor nightbeat risk-review to use check-readiness skill (0152)

## Morning review

Nightly consolidation runs via `/dream` (scheduled at 2 AM UTC via `/schedule 0 2 * * * /dream`).
Consolidation deduplicates memory across all projects using mem0 classifier + Park reflection.

To inspect consolidation results:
```
git log --grep='^dream:' --oneline
```

Each consolidation commit shows entry counts before/after (format: `dream: consolidate <project> memory (<n>→<m>)`).
Memory files that are marked DELETE receive a tombstone comment; git history provides recovery.

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules
