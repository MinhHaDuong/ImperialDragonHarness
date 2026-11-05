# Site practice: raids, review and merging

Procedures: skills merge, gaze, raid, verify-gate; `rules/workflow.md`. This
page records what happened when they ran. Author rulings:
[Commission](commission.md). Bracketed tags point to Sources.

## Current guidance

- **Tiers, since 2026-10-27.** Bookkeeping: mechanical checks, no review. Full: gaze, then verify-gate APPROVED. The before-merge record runs a cheap set (~13 s); the full suite runs after merge on main and a red there is ticketed, never reverted — a new failing test is folded under an open carrier ticket for the same check [opt][flows][1396]. Gate-less merges since 2026-10-26 were bookkeeping or author overrides [flows].
- **Land with `raid_land.py`**: it stages both sides of a ticket close (a hand `git add -u` once dropped ticket 1316 [1316]); close claims must be canonical — `**Ticket:** tickets/closed/...` recognised, leading `Closes tickets/...` not; `--ruled-claims -` lands a `Refs`-line PR (PR 2122) [dd72]. Sync local main after every merge [opt].
- **Gate records bind base tip and head.** Any merge into main or the close commit stales them: record again, retry once, then report, never loop [1246][cost]. Admission requires the rerolled head to be an ancestor of the new head (a rebased reroll fix gets a delta re-gaze first; 1403, PR 2149) [3d5ae7].
- **Ticket-only PRs** merge at once, unreviewed [1309].
- **Seats.** An executor's own gaze often records `seats: self-only`; the orchestrator's re-run found blocking defects on #1862, #1927, #2013 [1303][roster][29bf]. The cross-family requirement is gone (ruling 2026-10-31, PR 2085): family is a routing preference on seat lines, with the self-only refusal and "never called independent" [xfam]; mixed-panel measure +0.28 adopted findings per other-family seat (95% interval +0.11 to +0.45), confounded [xfam]. Seat parsing is one shared extractor: contradictory reach lines refused (PR 2115), Aider answer from the last framed marker (PR 2118) [bdf7]; a local seat's family is the served model's grid `family` (PR 2093); a `subagent` reason untrusts a forged `door=headless` header (PR 2102) [f3ac][2102]. Headless codex needs `< /dev/null` and a git review tree [roster][d225].
- **Rounds.** Judge findings against the bar fixed before review; fresh blockers at round 3 mean redesign. Long tails: #1676 (13 rounds, parked), #1559 (~8 h), #2013 (a new hole each round) [cost][vel][29bf]. Grep every restatement of a contract before delegating it (#1557).
- **A moved head voids review** [eve][1302]. GitHub can hold a PR head minutes behind the branch tip; close/reopen resyncs, then merge pinned to the ruled tip [bdf7].
- **Invocation.** verify-gate needs `repo=` and `session=` (17 of 103 lacked both); `merge-gate.py` wants the provider-qualified model id [flows][opt][1634]. Recheck raid premises first: 4 of 9 had cleared [vel][prem].

## Hazards

- `cmd | tail && git push --force-with-lease` pushed a half rebase (PR 1568) [fold]; `git reset --keep` dropped unpushed ticket commits [opt]; a chain force-pushed over a gated tip (#1493, no loss) [1136].
- Hunt adopted the orchestrator's worktree or ran in the raid's (1130, 1327, 1413) [fold][roster][late].
- A forced notes fetch can rewind `refs/notes/gate` so a push sends nothing; fixed in #2033 [1366].
- Full-suite failures that pass on rerun recur; cause not established [eve][hunt]. Gaze from another repo's cwd resolves PR numbers there: pass the worktree path and `--repo` [hunt]. A coder writing into the primary on main, then patching into its worktree, is the wrong order (t1381) [t1381].

## Open questions
- Attribution capture still mostly fails: no verbatim model id on Agent seats, missing `writer:` lines trip "fact order", script-only seats write no record (PRs 2094, 2105, 2153, 2155, 2156) [1307][t1396]. Author: "still not smooth" (2026-10-29). Gaze wall time ~42 % setup/closing; a faster orchestrator waits on arena data. Auto-merge waited ~7 min after green (#1472, #1414, #1324): cause not established [cat].
## Retired

- Merge-helper mechanics (`erg-pr-merge` etc., #1533): helper deleted, ticket 1178 [fold].
- 15-file un-reviewable breaker and overrides (#1179, #1060, #1538 stack): wall down, PR 1614 [fold].
- Overrides list 2026-10-03 to 10-13 (#1157, #1187, #1235, #1245, #1253, #1348, #1372, #1374): history; current path is merge § Gating tiers plus Commission.
- Degraded panels via silent child cap, Pi `/review`, session isolation guard (10-02 to 10-13): superseded by the headless seat door and `seats:` evidence (1301, 1326). Invented "operator-approved" waiver (raid 1072): verdict discarded, history.
- Attribution counts 2026-10-05 to 10-13: telemetry, `memory/evidence/attribution/`.
- Tracker-0205 author statement: moved to Commission.
- TMPDIR-inside-worktree failures: `test_project_census` passes with TMPDIR under `.tmp/` (2026-10-30, 14 passed); hook tests fixed in #1688.
- 2026-10-13 to 10-15 integration notes (#1403 close grammar, Arena force-merge, 1098 DEGRADED): history; current grammar in `claims.md`.
- Escalation and wait lines: restatements of `rules/workflow.md` and `rules/coding-bash.md`, pruned as duplicates (smelt 2026-10-30); rulings kept in Commission.
- "Other-family seats caught defects, no catch rate measured: a hypothesis" (smelt 2026-10-30): measured 2026-10-31 (+0.28/seat, confounded); the gate was removed by ruling the same day (PR 2085).

## Sources

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
[opt]: ../journal/2026/2026-10-27-raid-optimistic-merge-afternoon.md
[flows]: ../journal/2026/2026-10-28-review-gate-flows-pr1863.md
[1316]: ../journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md
[1246]: ../journal/2026/2026-10-27-raid-sitrep-ticket-1246.md
[cost]: ../journal/2026/2026-10-27-review-cost-raid-and-redesign.md
[1309]: ../journal/2026/2026-10-29-tracker-1309-closed.md
[1303]: ../journal/2026/2026-10-28-raid-1303-pr1862.md
[roster]: ../journal/2026/2026-10-28-raid-534413-wait-roster-pr1927.md
[29bf]: ../journal/2026/2026-10-29-raid-29bf18-gaze-close-and-deletion-path.md
[d225]: ../journal/2026/2026-10-30-raid-d2253c-gaze-seat-evidence.md
[vel]: ../journal/2026/2026-10-21-velocity-raid-1167-1169.md
[eve]: ../journal/2026/2026-10-26-evening-review-ceremony.md
[1302]: ../journal/2026/2026-10-28-raid-1302-1306-wrapup.md
[1634]: ../journal/2026/2026-10-23-review-merge-1634-1635.md
[fold]: ../journal/2026/2026-10-21-gate-on-folds-and-wall-down.md
[1136]: ../journal/2026/2026-10-20-raid-1136-1137-1126-and-1100-split.md
[1366]: ../journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md
[hunt]: ../journal/2026/2026-10-27-hunt-phases-1235-override-merge.md
[1307]: ../journal/2026/2026-10-28-raid-1307-1308-pr1874-pr1876.md
[prem]: ../journal/2026/2026-10-29-ready-ticket-review-premise-check.md
[cat]: ../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md
[xfam]: ../journal/2026/2026-10-31-cross-family-gate-dropped.md
[bdf7]: ../journal/2026/2026-11-01-raid-bdf7dd-2fb774-seat-parsing.md
[f3ac]: ../journal/2026/2026-10-31-raid-f3ac96-seat-identity.md
[2102]: ../journal/2026/2026-10-31-t1396-seat-forgery-regression.md
[3d5ae7]: ../journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md
[dd72]: ../journal/2026/2026-10-31-raid-dd72df-t1402.md
[t1396]: ../journal/2026/2026-10-31-t1396-session-identity-leak.md
[t1381]: ../journal/2026/2026-10-31-t1381-result-names-checks.md
[late]: ../journal/2026/2026-11-01-raid-1f0534-late-merges.md

Also examined, no claim kept: [1390 evidence](../journal/2026/2026-10-14-pr1390-review-evidence.md), [healthcheck](../journal/2026/2026-10-15-morning-healthcheck-merges-ticket-revalidation.md), [1456](../journal/2026/2026-10-19-pr1456-review-and-attribution.md), [1150](../journal/2026/2026-10-20-raid-1150-and-1146-integration.md), [1153 stack](../journal/2026/2026-10-21-1153-stack-landed.md), [waits](../journal/2026/2026-10-21-await-external-probes.md), [1170](../journal/2026/2026-10-21-raid-1170-1173-1175.md), [stack](../journal/2026/2026-10-21-raid-stack-and-merge-helper.md), [1212](../journal/2026/2026-10-26-raid-1212-1211-1221-1219-1220-1215.md), [capture-pr](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md), [1732](../journal/2026/2026-10-27-erg-sync-molt-step-1732.md), [1214](../journal/2026/2026-10-27-raid-1214-1218-waiting-follies.md), [1841](../journal/2026/2026-10-27-roar-1841-watchlist-closures.md), [run-pool](../journal/2026/2026-10-31-t1396-run-pool-throttle.md), [wrapup](../journal/2026/2026-11-01-raid-1f0534-wrapup.md), [wave 3](../journal/2026/2026-11-01-raid-1f0534-wave3-pi-agents.md).
Previous page's 2026-10-02 to 10-15 episodes are in git: `git show HEAD:memory/topics/raid-review-and-merge.md`.
