---
date: 2026-10-30
kind: episode
project: .agents
refs: [PR 2054, PR 2060, PR 2061, PR 2062, ticket 1375, ticket 1378, ticket 1379]
---

# Raid 0da24b: owned failure fields, branch-review carry-over

Context: raid over tickets 1378 and 1379, resumed by an Opus 5.5 team lead from a handoff after the interface session ran out of context. Executors were Sonnet 5.5 coder subagents (1378 before the handoff, 1379 after).

Events:
- 1378 (PR #2060): verify-gate round 1 returned REROLL on the criterion "PR #2054 is closed unmerged", which the ticket's own plan scheduled after the merge. #2054 was closed with a pointer, round 2 on the same code returned APPROVED. `erg log 1378` refused the closed ticket ("no ticket found"); the bump note was appended by hand to `tickets/closed/1378-*.erg`.
- `raid_land.py 2060` merged (4269e12e) but printed `attribution: invalid: line 6: invalid repository-relative anchor: scripts/gaze_close.py:cleanup-blocked branch`; the PR body has no attribution block and `--capture-unit pr:2060` refuses the same line. A gaze answer cited a finding without a line number.
- 1375 closed in ticket-only PR #2061 (bb5839b8) on 1378 plus the author's won't-fix ruling; its first landing attempt was refused because the body said "Closes ticket 1375." instead of a `**Ticket:**` line.
- 1379 (PR #2062): the executor's head 74b03716 was REVIEWED but fitted the 18350-char resident-rules budget (`tests/test_rules_resident_budget.py`) by deleting four unrelated `rules/workflow.md` clauses (repeat-yourself stop, null-result scope, clean-room render, 15-file signal); that gaze's intent did not cover them. The raid restored them (b7279354), moving step-2 procedure into `skills/merge/SKILL.md` § Gating tiers. A narrower gaze (openai gpt-6.1-sol seat) found a lost prohibition ("never forked or delegated" became "never delegated"); 938db2e0 restored it as "never branched or delegated", paying 12 chars from steps 2-3's own wording. The fix-and-regate breaker escalates a doc fix at that point; an advisor (Fable, one-shot) agreed to one more narrower gaze under escalation step 1, recorded on the PR. It returned REVIEWED; verify-gate round 1 APPROVED on 973dc3dd; merged be17d433.

Outcome: tickets 1375, 1378, 1379 closed; PR #2054 closed unmerged; `make check` on be17d433 in a detached worktree: 3192 passed, 4 skipped. Review attribution for #2060 not captured (refused anchor); #2062 captured.
