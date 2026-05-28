# Imperial Dragon Harness — State

Last updated: 2026-05-28T11:51Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-28T11:51Z -->

**Tickets:** 3 ready · 5 blocked — `erg ready tickets/` for full list
**Recent commits:**
  01720db tickets: close 0173 — fix landed in #216 (#217)
  a5954c2 fix(0173): pretooluse-worktree-path-guard resolves cwd from PreToolUse JSON (#216)
  0ef401a Merge pull request #215 from MinhHaDuong/claude/erg-ready-presentation-BJhbR
  85d41f8 test(0168): assert malformed-JSON guard stays silent on stderr
  25f8152 fix(0168-0169): harden worktree tooling from opus-panel findings

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
