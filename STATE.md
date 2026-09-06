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
- **Abandoned starts on origin, all on still-open ready tickets**: `t0359-…`, `t0425-…`, `t0500-…`, `t393-…`, `memory-rtk-mechanism-correction`, 1–4 commits each from 2026-08-14, with a worktree each. Check them before re-attacking those tickets. `t-idh-mergeeffect` and `tickets/raid-0537-harness-findings` are long-diverged.

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
