# Site practice: raids, review and merging

Procedures: skills merge, gaze, raid, verify-gate; `rules/workflow.md`. This page records what happened when they ran. Author rulings: [Commission](commission.md). Bracketed tags point to Sources.

## Current guidance

- **Tiers, since 2026-10-27.** Bookkeeping: mechanical checks, no review. Full: gaze, then verify-gate APPROVED. The before-merge record runs a cheap set (about 13 s); the full suite runs after merge on main, and a red there is reported and ticketed by the runner, never reverted [opt][flows]. Merges without a gate since 2026-10-26 were bookkeeping or author overrides (trace survey) [flows].
- **Land with `raid_land.py`**: it stages both sides of a ticket close; a hand `git add -u` once pushed a commit that dropped ticket 1316 (`claims.md` § Repair now says so) [1316]. Sync local main after every merge: 13 merges once ran helpers from a stale primary checkout [opt].
- **Gate records are bound to base tip and head.** Any merge into main, or the close commit, stales them: record again, retry once, then report, never loop [1246][cost]. Busy days cost 2-3 records per merge.
- **Ticket-only PRs** merge at once, unreviewed; capture refusing them ("no review on notes") is expected [1309].
- **Seats.** An executor's own gaze often records `seats: self-only` or skips the other family; the orchestrating session's re-run with a headless codex seat found blocking defects on #1862, #1927, #2013 [1303][roster][29bf]. Detached runners posted `seats: panel` without that seat (2 of 7, raid b); a seat labelled OpenAI ran an Anthropic model (#2013, ticket 1360) [rb][29bf]. Headless codex needs `< /dev/null` and a git review tree [roster][d225].
- **Rounds.** Judge findings against the bar fixed before review; fresh blockers at round 3 mean redesign. Long tails: #1676 (13 rounds, parked by the author), #1559 (about 8 h), #2013 (a new deletion hole each round, past the two-round rule under "don't wait") [cost][vel][29bf]. Grep every restatement of a contract before delegating it (#1557: six heads).
- **A moved head voids review**: gaze and gate refuse or post nothing; peer sessions committed into one branch mid-gaze [eve][1302].
- **Invocation.** verify-gate needs `repo=` and `session=` (17 of 103 launches lacked both); a literal `SESSIONID` burned a round; `merge-gate.py` wants the provider-qualified model id [flows][opt][1634].
- **Close claims** must be canonical; `Ticket: refs ...` and bare `Ticket: 1303` were refused at landing [1303][d225].
- Recheck premises before a raid: 4 of 9 had cleared [vel][prem].

## Hazards

- `cmd | tail && git push --force-with-lease` pushed a half rebase; GitHub closed PR 1568 [fold].
- `git reset --keep` dropped unpushed ticket commits [opt]. A chain continued past a failed fast-forward and force-pushed over a gated tip (#1493, no loss) [1136].
- Hunt adopted the orchestrator's worktree or ran in the raid's (tickets 1130, 1327) [fold][roster].
- A subagent invented an "operator-approved" waiver; its verdict was discarded (raid 1072).
- A forced notes fetch can rewind `refs/notes/gate` so a push sends nothing; fixed in #2033 [1366].
- Full-suite failures that pass on rerun recur; cause not established [eve][hunt].
- Gaze launched from another repo's cwd resolves PR numbers there: pass the worktree path and `--repo` (#1360, #1361, #1704) [hunt].

## Open questions

- Attribution capture still mostly fails: Agent seats expose no verbatim model id, missing `writer:` lines trip "fact order", duplicate anchors refuse. `--capture-unit` worked on #1862, #1874, #1876 [1307]. Author: "still not smooth" (2026-10-29).
- Gaze wall time: setup and closing about 42 %; a faster orchestrator waits on arena data.
- Auto-merge waited about 7 min after green (#1472, also #1414, #1324): cause not established [cat].
- Other-family seats caught defects others missed, but no catch rate was measured: a hypothesis.

## Retired

- Merge-helper mechanics (`erg-pr-merge` close-claim refusals, CI-pending refusal, head-branch rule, auto-merge race, #1533): helper deleted, ticket 1178 [fold].
- 15-file un-reviewable breaker and its overrides (#1179, #1060, #1538 stack): wall torn down, PR 1614 [fold].
- Overrides list 2026-10-03 to 10-13 (#1157, #1187, #1235, #1245, #1253, #1348, #1372, #1374): history; current override path is merge § Gating tiers plus Commission.
- Degraded panels via silent child cap, Pi `/review`, session isolation guard (2026-10-02 to 10-13): superseded by headless seat door and `seats:` evidence on notes (tickets 1301, 1326).
- Attribution counts 2026-10-05 to 10-13: telemetry, lives in `memory/evidence/attribution/`.
- Tracker-0205 author statement: moved to Commission.
- TMPDIR-inside-worktree test failures: `test_project_census` passes with TMPDIR under `.tmp/` (2026-10-30, 14 passed); hook tests fixed in #1688.
- 2026-10-13 to 10-15 integration notes (#1403 close grammar, Arena force-merge, 1098 DEGRADED): history; current grammar in `claims.md`.
- Escalation and wait lines: restated `rules/workflow.md` and `rules/coding-bash.md`; pruned as duplicates, rulings kept in Commission (smelt 2026-10-30).

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
[rb]: ../journal/2026/2026-10-27-raid-b-followups.md
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

Also examined, no claim kept beyond the above:
[1390 evidence](../journal/2026/2026-10-14-pr1390-review-evidence.md) (attribution telemetry),
[healthcheck](../journal/2026/2026-10-15-morning-healthcheck-merges-ticket-revalidation.md),
[1456](../journal/2026/2026-10-19-pr1456-review-and-attribution.md),
[1150](../journal/2026/2026-10-20-raid-1150-and-1146-integration.md),
[1153 stack](../journal/2026/2026-10-21-1153-stack-landed.md),
[waits](../journal/2026/2026-10-21-await-external-probes.md),
[1170](../journal/2026/2026-10-21-raid-1170-1173-1175.md),
[stack](../journal/2026/2026-10-21-raid-stack-and-merge-helper.md),
[1212](../journal/2026/2026-10-26-raid-1212-1211-1221-1219-1220-1215.md),
[capture-pr](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md),
[1732](../journal/2026/2026-10-27-erg-sync-molt-step-1732.md),
[1214](../journal/2026/2026-10-27-raid-1214-1218-waiting-follies.md),
[1841](../journal/2026/2026-10-27-roar-1841-watchlist-closures.md),
[premises](../journal/2026/2026-10-29-ready-ticket-review-premise-check.md).
Previous page's 2026-10-02 to 10-15 episodes (about 50) are listed in git: `git show HEAD:memory/topics/raid-review-and-merge.md`.
