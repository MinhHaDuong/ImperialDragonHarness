---
date: 2026-11-01
kind: episode
project: .agents
refs: [PR 2150, PR 2151, PR 2161, PR 2155, ticket 1405, ticket 1394, ticket 1413, ticket 1417]
---

# Raid 1f0534, later outcomes: PR 2150 merged, 2151 and 2161 parked

Appended after `2026-11-01-raid-1f0534-wrapup.md`, which covers the six earlier merges.

Observable events:
- PR 2150 (ticket 1405, Pi skill case notes; it also logged stage 4 on ticket 1394) merged as a5fd217e168f. It needed a rebase onto main after PR 2155 landed, with a conflict in the test file (resolved as the union of the Codex and Pi tests). It was re-gazed narrow and gated APPROVED in round 1. `raid_land.py --cleanup` removed its worktree and branch.
- PR 2151 (ticket 1417, phase 2 audit) parked: its narrow gaze returned FINDINGS on the audit fixes (stale 9/6 counts); the counts were fixed on the branch as bookkeeping, and it awaits the author.
- PR 2161 (ticket 1413, runtime rules generator) gated NEEDS-AUTHOR: criteria 1 and 3 need the host install and a sentinel re-probe.
- The ticket 1413 coder worked inside the raid orchestrator's own worktree instead of making its own.
