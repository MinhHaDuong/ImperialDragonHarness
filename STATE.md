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
- **0872 triaged 2026-09-07 — the five abandoned starts of 14 August are no longer the only copy of anything**: every one is preserved under an `archive/<branch>` tag on origin, so nothing below is irreversible. Three revived onto today's main with merge requests open — #810 (0359, clean cherry-pick, negative control fired), #811 (0500, one real conflict against main's "first roar" paragraph), #813 (0393, reconciled with 0870 rather than merged over it). `memory-rtk-mechanism-correction` dropped: main's 2026-08-14 15:44 synthesis commit already retracts the `--no-merges` cause the branch asserts. `t0425` (typo axis) is the one left standing — the work is good and main has none of it, but it edits `scripts/inject_rule_on_edit.py`, which a parallel executor owned that night, and it adds `last-reviewed:` stamps the run was told not to touch. Tickets 0359, 0425, 0500 and 0393 all stay OPEN. **Manual step left:** five 14-August worktree registrations and their local branches still need pruning (`agent-acb24c39f94523736`, `agent-a45d137e93534fd90`, `agent-aafc5891c9ca4c5a7`, `agent-afd83aa4529d1f611`, `mem-rtk-fix`) — the run was forbidden to remove worktrees with other sessions live.
- **A three-week-old branch is measured against today's main, never against its own base**: 0872 recorded `t393` as merging *clean* into `reviewers.sh` on 2026-09-06 and warned that the clean exit was the trap. One day later it conflicts instead — main moved again. The warning was right about the shape and wrong about the fact, which is the general lesson: a merge verdict recorded in a ticket expires, and the marker grep plus the suite are what settle it either way.
- **Worktree git, settled 2026-09-06** (harness memory, promoted): two guards refuse git in a worktree session, not one. `\git` beats the rtk rewrite and is cheaper than `/usr/bin/git`; neither beats the containment refusal on `-C`, which only a script file reaches. The guard reads command text, not intent, and a refusal takes the whole compound with it.

## Backlog

- Streamline settings.json hook configuration
- Merge REALF guidelines and business rules
