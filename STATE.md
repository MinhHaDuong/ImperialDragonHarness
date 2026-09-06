# Imperial Dragon Harness — State

Last updated: 2026-09-06T22:18Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines. The harness itself is the deliverable.

## Status
<!-- generated 2026-09-06T22:18Z · as of c0c42fc -->

**Tickets:** 17 ready · 8 blocked — `erg ready tickets/` for full list
  next: 0207 Agnostic CLI reviewer seat — one config, OpenRo… · 0359 Spawn bash test children hermetically (env -i) …
**In flight:** 4 open PRs (1 draft), oldest #780 9d · CI main: success
**Recent (first-parent):**
  c0c42fc Merge pull request #802 from MinhHaDuong/hk-ask-the-live-peer
  d352851 Merge pull request #801 from MinhHaDuong/hk-promote-worktree-git-guard
  3354552 Merge pull request #800 from MinhHaDuong/hk-consolidate-worktree-guard-notes

## Blockers

(none)

## Next actions
- **Cool-down doctrine in force** (2026-07-14): file a tooling ticket only if the defect blocks a merge, corrupts state, or bites a science project; throughput points at the science repos.
- **External-reviewer advisory trial LIVE, hands-free**: openrouter-frontier and openrouter-budget seats in `skills/reviewers/panel.yml`; /gaze requests, harvests, scorecards them (PR #638). Data accrues on ticket 0207 (≥5 MRs across ≥3 projects per config, then the author's promote/drop call). 0205 tracker and 0356 wait on that verdict.
- **0062 trigger**: re-open Firecracker isolation when IDH agents run against secret-bearing projects.
- **Lint gate has no holes** (2026-08-26, 0470 + 0590): `.ruff.toml` carries no suppression; reopening one is argued in a ticket, not slipped into config.
- **0610 open**: hook scripts swallow every exception and exit 0, so 17 of 31 hook tests pass with the script fully broken. Fix is a test-only strict mode; see the ticket for the closed-`env` trap.
- **0572 filed** (2026-09-06, from the author's 2026-08-22 note): rule files drift by accumulation; trim `workflow.md`, split Claude Code idiosyncrasies from the core, make the review cadence catch growth.
- **Catch-up 2026-09-06 closed**: the whole queue merged (#786–#802), the primary checkout went from 30 dirty paths to clean, and 11 worktrees, 19 local and 6 remote branches were removed. Ticket 0870 landed the reviewers fix that had sat uncommitted since 3 September; 0572 is now valid erg and wants the author's amendment. Still open and both the author's call: #780 (0802 perch adapters, draft, 18 tests green) and #794 (0871, another session's).
- **0872 filed — five abandoned starts of 14 August**: branches `t0359-…`, `t0425-…`, `t0500-…`, `t393-…` and `memory-rtk-mechanism-correction`, 81 to 560 lines each, every one the only copy of its commits and four naming still-open ready tickets. Triage before re-attacking any of them. `t393` overlaps the 0870 fix to `reviewers.sh` and merges clean while doing so, so grep the result for the 0870 markers.
- **Worktree git, settled 2026-09-06** (harness memory, promoted): two guards refuse git in a worktree session, not one. `\git` beats the rtk rewrite and is cheaper than `/usr/bin/git`; neither beats the containment refusal on `-C`, which only a script file reaches. The guard reads command text, not intent, and a refusal takes the whole compound with it.

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
