# Imperial Dragon Harness — State

Last updated: 2026-09-06T16:46Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-06T16:46Z · as of de54908 -->

**Tickets:** 16 ready · 8 blocked — `erg ready tickets/` for full list
  next: 0207 Agnostic CLI reviewer seat — one config, OpenRo… · 0359 Spawn bash test children hermetically (env -i) …
**In flight:** 5 open PRs (1 draft), oldest #780 8d · CI main: success
**Recent (first-parent):**
  de54908 memory(home): 3 notes from 1-2 September left uncommitted in the primary checkout
  6a31411 memory: two new project folders (corpus-access-bench, secretariat rapports d'activité), 3 notes each
  99ade18 memory(polycentric-activity): 11 notes from 19-30 August left uncommitted in the primary checkout

## Blockers

(none)

## Next actions
- **Cool-down doctrine in force** (2026-07-14): file a tooling ticket only if the defect blocks a merge, corrupts state, or bites a science project; throughput points at the science repos.
- **External-reviewer advisory trial LIVE, hands-free**: openrouter-frontier and openrouter-budget seats in `skills/reviewers/panel.yml`; /gaze requests, harvests, scorecards them (PR #638). Data accrues on ticket 0207 (≥5 MRs across ≥3 projects per config, then the author's promote/drop call). 0205 tracker and 0356 wait on that verdict.
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects.
- **Lint gate has no holes** (2026-08-26, 0470 + 0590): `.ruff.toml` carries no suppression; reopening one is argued in a ticket, not slipped into config.
- **0610 open**: hook scripts swallow every exception and exit 0, so 17 of 31 hook tests pass with the script fully broken. Fix is a test-only strict mode; see the ticket for the closed-`env` trap.
- **0572 filed** (2026-09-06, from the author's 2026-08-22 note): rule files drift by accumulation; trim `workflow.md`, split Claude Code idiosyncrasies from the core, make the review cadence catch growth.
- **Catch-up 2026-09-06**: 5 queued PRs merged, 11 stale worktrees and 15 merged branches removed. Still open: #780 (0802 perch adapters, draft, author's call), #791 (dream 09-04, conflicts with #788, needs a rebase).
- **0872 filed — five abandoned starts of 14 August**: branches `t0359-…`, `t0425-…`, `t0500-…`, `t393-…` and `memory-rtk-mechanism-correction`, 81 to 560 lines each, every one the only copy of its commits and four naming still-open ready tickets. Triage before re-attacking any of them. `t393` overlaps the 0870 fix to `reviewers.sh` and merges clean while doing so, so grep the result for the 0870 markers. The two long-diverged branches are gone: `t-idh-mergeeffect` and `tickets/raid-0537-harness-findings` each held one commit whose tickets (0272, 0248, 0249) are closed on main and whose code landed by another route, verified line by line before deletion on 2026-09-06.

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
