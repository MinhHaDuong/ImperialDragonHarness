# Imperial Dragon Harness — State

Last updated: 2026-05-29T15:20Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-29T15:20Z -->

**Tickets:** 5 ready · 5 blocked — `erg ready tickets/` for full list
**Recent commits:**
  c121599 Merge pull request #228 from MinhHaDuong/t176-grep-e-guard
  0ccc4eb ticket(0176): close and archive — PR #228
  c67d99c feat(0176): add grep-e-guard CI job — no grep -E/-G with PCRE escapes
  2289e7a Merge pull request #227 from MinhHaDuong/t179-refresh-state-path-arg-v2
  4c3e311 Merge origin/main into t179 to resolve post-close-commit conflicts

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
