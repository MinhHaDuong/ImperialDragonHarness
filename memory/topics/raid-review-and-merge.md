# Site practice: raids, review and merging

Authority: merge, gaze, raid, verify-gate and `rules/workflow.md`.
Rulings: [User rulings][source1]. Tags refer to source episodes.

## Current guidance

- Bookkeeping has mechanical checks without review; full tier has gaze then verify-gate APPROVED. The cheap before set precedes merging; full suite follows on main. Red is ticketed, not reverted; same-check failures can fold into a carrier [opt][flows][1396]. Gate-less past merges were bookkeeping or author overrides.
- `raid_land.py` stages both sides of a close; hand `git add -u` dropped 1316 [1316]. Canonical close claims use `**Ticket:**`; leading `Closes tickets/...` fails [dd72]. Even “new; filed, not closed” on a Ticket line closed-claims a filing: use a Refs line and `--ruled-claims -` [filing]. Ticket-only PRs go to merge at once; sync main after each merge [1309][opt].
- Gate records bind base and head; a main merge or close commit stales them. Re-record and retry once, then report [1246][cost]. Reroll admission requires ancestry; rebased fixes get delta gaze first (1403) [3d5ae7]. Branch gaze carries to the PR for the same head plus bookkeeping only [carry].
- Self-only gaze is accepted by the current merge skill; a panel is preferred, never required. Historical reruns caught blockers (#1862/#1927/#2013) [1303][roster][29bf]. Cross-family enforcement is removed; family remains a routing preference, shared-family is never independent [xfam]. The +0.28 findings/seat estimate (95% interval +0.11..+0.45) is confounded, not a causal benefit.
- Seat parsing rejects contradictory reach lines; Aider uses the last framed marker [bdf7]. Local family comes from the served model's grid row [f3ac]; a subagent reason untrusts a forged headless header, while free text keeps the 1388 behavior [2102]. Headless Codex needs closed stdin and a review tree [roster][d225]. Requested pins do not establish masked served identity [train].
- Review's bar is fixed before rounds; fresh blockers at round 3 mean redesign. Long tails (#1676 13 rounds parked; #1559 ~8 h; #2013 neighboring holes) are observed costs [cost][vel][29bf]. Grep all contract restatements before delegation (#1557).
- A moved head voids review; forge head lag once needed close/reopen, then a merge pinned to the ruled tip [eve][1302][bdf7]. `verify-gate` needs repo/session (17/103 omitted both); merge-gate needs a provider-qualified model [flows][1634]. Recheck premises: 4/9 had cleared [prem].

## Hazards

- Piped exit codes pushed a half rebase (#1568); reset --keep lost unpushed tickets; force-push crossed a gated tip (#1493, no loss) [fold][opt][1136]. Hunt adopted another session's tree (1130/1327/1413); t1381 wrote primary first [late][t1381].
- Forced notes fetch can rewind a gate append so ref-name push sends nothing [1366]. Foreign cwd resolves PR numbers there: pass worktree/repo [hunt]. Full-suite failures recur after isolated greens, cause unknown [eve]. Restricted access once emitted unreadable notes and a conflict; the same pinned head admitted with required access, without a code fix [train].

## Open questions

Attribution still has unavailable writer identities, fact-order failures and script-only gaps [t1396][identity]. Gaze setup/closing consumed ~42%; faster orchestration awaits arena data. Auto-merge once waited ~7 min after green; cause unknown [cat].

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
[1396]: ../journal/2026/2026-10-31-t1396-seat-forgery-regression.md
[filing]: ../journal/2026/2026-11-05-pr2223-filing-pr-ticket-line-parsed-as-close-claim.md
[carry]: ../journal/2026/2026-10-30-raid-0da24b-scrub-fields-and-review-carry-over.md
[train]: ../journal/2026/2026-11-07-raid-train-controls.md
[identity]: ../journal/2026/2026-11-05-pr2217-attribution-capture.md

[source1]: user-rulings.md

## Fallback
