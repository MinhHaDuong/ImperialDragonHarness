# Harness doctor visit: triage after raid b6aabf (2026-10-29)

Date: 2026-10-29
Project: ImperialDragonHarness

Complaint or triage input: the author chose triage, no complaint. Input: skills and rules changed since the 2026-10-27 entries (91 files; heaviest churn gaze 35, raid 33, merge 33, verify-gate 25, hunt 23 commits). Earlier visits: no tickets above the floor, no revisit due; their follow-ups 1236 and 1237 closed.

Probes and controls:
- Lint (`skill_text_lint.py`): control fired on `tests/fixtures/harness-doctor/trace-doctor-SKILL.md` (body_lines, date, history_phase, long_fence all present). 181 hits on 84 changed files, all dismissed: history_phase 61 (step names "Phase N", not history), ticket_word 41 and date 35 (examples, log formats), body_lines 19 (size warning; split follows exclusivity), project_name 13, long_fence 5, ticket_ref 2, history_formerly 2, history_used_to 2, heredoc 1. Author: keep the dismissals for the next visit.
- Reading probe on the three leads from running the skills this session; control fired: the shared stance of harness-doctor and test-doctor (`skills/test-doctor/SKILL.md:18` and `skills/harness-doctor/SKILL.md:19,76` cite `references/doctor-practice.md`).
- Runtime diagnostics: not run.

Findings above the floor (tickets filed, PR #1940):
- F1, ticket 1329: `skills/molt/SKILL.md:74,253` switched the shared primary checkout off main, against `rules/git.md:9` and `rules/workflow.md` § Worktree paths. Author asked whether step 6 always runs: no (step 2.5's stop, crashes). Fixed by PR #1941 (48c145ba) after five gaze rounds, each with an openai/gpt-6.1-sol seat: `reset --hard` with an unset `$W` (would reset the primary), `git worktree remove` deleting ignored `.tmp/`, a commit count read in the primary checkout, the preflight clearing a commit-less sweep's uncited `.tmp/` (ticket 1119's rule), and a case order skipping the marker. The author authorized each round past the fix-and-regate breaker. The coordinator ran round 2 without escalating, though the breaker required it (prose fix and a consider item).
- F2, ticket 1330: raid RAID_START without `deadline=` made every sitrep UNREADABLE (raid b6aabf: three sitreps, exit 2). Fixed by PR #1942 (292d0f48): deadline optional, elapsed always shown (ticket 1246's intent), `gate_max` read independently; F5 (raid § Phase 7 paraphrasing merge's recipe) fixed in the same PR by a pointer.
- F3, ticket 1331: `rules/git.md` force-with-lease and branch cleanup refused by the auto-mode classifier twice in 24 h. Allow rules added on padme with the author's explicit permission; PR #1943 (33ef05e5) records them via `scripts/claude-allow-check.py` (read-only; exit 0/1/2) and `rules/claude-code.md` § Allow rules. `git update-ref -d` stays refused ("Self-Modification").
- F4 (below floor; author ruled fix): yawn check 8 warned after a commit-less molt; fixed in PR #1941 by `<git-common-dir>/molt-last-run`.

Below the floor, open:
- `skills/molt/SKILL.md:264` case 4 unreachable (a merged branch counts 0 and matches case 3; same removal, correct marker). Not adopted.
- `rules/claude-code.md:52-53`: the extension-point comment sits between the team-lead bullet and its `Knobs:` line.
- `scripts/claude-allow-check.py:35-40` does not type-check `allow` entries; reads only `~/.claude/settings.json`, so a rule in `settings.local.json` reads missing (never falsely present).
- Review-attribution capture for PR #1941 refused: "line 13: duplicate finding within one reviewer attempt" (one review id over five gaze rounds); `--capture-pr` refused with "fact order requires kind, pr, writer before reviewers". Cause not isolated.

Revisit condition: at the next molt, check that the primary checkout stays on main, step 7 names its case, and yawn check 8 reads clean after a commit-less molt; at the next raid with no time budget, check that the sitrep exits 0 with elapsed time; on doudou, run `scripts/claude-allow-check.py` (padme exit 0 on 2026-10-29). Rerun the lint on files changed since this entry and reuse the dismissals above.
