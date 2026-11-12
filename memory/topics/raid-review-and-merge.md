# Site practice: raids, review and merging

Authority: merge, gaze, raid, verify-gate and `rules/workflow.md`.
Rulings: [User rulings][source1]. Tags refer to source episodes.

## Current guidance

- Bookkeeping has mechanical checks without review and runs no test suite; full tier has gaze then verify-gate APPROVED. Full suite follows on main; red is ticketed, not reverted [opt][flows]. A close that archives a ticket moves its file: grep `memory/` and `design/` for its open path first (1506 painted main red) [morn].
- `raid_land.py` stages both sides of a close [1316]. Canonical close claims use `**Ticket:**`; a filing names its ticket on a Refs line [filing][dd72]; `Ticket: none` is not canonical (REROLL, 2351) [2351]. `--ruled-claims` must equal the body's claims even at bookkeeping tier [829e]. Ticket-only PRs go to merge at once.
- Gate records bind base and head; a main merge or close commit stales them; re-record and retry once [1246]. A sibling merge between gaze and gate voids the verdict: the gate refuses a tip that no longer merges cleanly, and a rebase changes the range patch-id ("no gaze answer covers"). Merging main into the branch (no rebase) plus a narrow gaze on the merge commit recovered in 14 min [2402][45e1][1479]. Two wave PRs sharing a rebased annotation commit conflict on the second merge [45e1].
- Raid Phase 2: per-ticket reimagine at the lead's judgment; the Blind-Spot pass always runs (author, 1417) [morn]. It changed the plan materially in most November raids (sites a grep missed, a stranding exit check, second corpora) [88e7][632b][1488][4afd][91a3][13f6][3429].
- Gaze of gate, merge or review machinery plans an other-family seat (`decorrelation.md`); family is a preference, shared-family is never independent [xfam]. A coder's nested self-only gaze on such code got a second gaze with an OpenAI seat (2378, 2428) [2378][ce1c]. A seat that fails to start leaves a self-only answer: rerun for the planned seat (2399 then found a real defect) [f7aa]. A Codex seat launched as `gpt-6-luna` reported `gpt-6.1-sol` and cited the lead's tree, not the head [45e1]. The +0.28 findings/seat estimate is confounded.
- Review's bar is fixed before rounds; fresh blockers at round 3 mean redesign; a third fix round is the author's [cost][1495]. Recheck premises: 4/9 had cleared; 1487's premise did not match the tree [prem][a8b3].
- Verify-gate rules NEEDS-AUTHOR when the author's ruling exists only in conversation: agent records carry git name `reviewer` and the author's forge login. A PR comment quoting the turns settled 2442 [2442].

## Hazards

- The classifier refused gated `raid_land.py` landings as "Merge Without Review" in interface sessions (2346, 2367, 2378, 2397, 2441) and a delegate briefed to retry; they ran once the author named the PR. Landings ran unrefused when gaze and gate ran in the same session (2402, 2414, 2428, 2436). A yes given before the PR had a number did not count (2397) [5c2a][2397][morn]. A "Harness Gated Merge" allow rule was added 2026-11-10 on both hosts; its effect is not established [2378].
- Piped exit codes pushed a half rebase (#1568); hunt adopted another session's tree; a coder skipped hunt's worktree and committed on the raid session branch (1511) [fold][late][13f6]. A rebase replays annotation commits, so WAVE_BASE stops being an ancestor [1483].
- Restricted access once emitted unreadable notes; the same head admitted with required access [train]. A forced notes fetch can rewind a gate append [1366]; a foreign cwd resolves PR numbers there [hunt]; full-suite failures recur after isolated greens, cause unknown [eve].

## Open questions

Attribution: "not derivable" when gaze notes carry no `reviewer:` line or the lead skipped `writer:`; `adopted:` flags were wrong both ways (2358, 2365, 2397) [2365][88e7][61f5]. Gaze setup/closing consumed ~42%; faster orchestration awaits arena data.

## Sources

- Provenance: [source inventory](../../design/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../design/memory-v8/source-revisions.tsv).
- Carried from the previous page, still in their episodes: seat parsing and reach lines [bdf7], local family from the grid row [f3ac], forged headless header [2102], headless Codex stdin [d225], reroll ancestry and delta gaze [3d5ae7], branch gaze carry-over [carry], long tails and contract greps [vel][29bf], moved head and forge lag [eve][1302], verify-gate repo/session [1634], forced notes rewind [1366], foreign-cwd PR resolution [hunt], unexplained full-suite failures [eve], auto-merge delay [cat], historical reruns [1303][roster].
[opt]: ../journal/2026/2026-10-27-raid-optimistic-merge-afternoon.md
[flows]: ../journal/2026/2026-10-28-review-gate-flows-pr1863.md
[1316]: ../journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md
[1246]: ../journal/2026/2026-10-27-raid-sitrep-ticket-1246.md
[cost]: ../journal/2026/2026-10-27-review-cost-raid-and-redesign.md
[1303]: ../journal/2026/2026-10-28-raid-1303-pr1862.md
[roster]: ../journal/2026/2026-10-28-raid-534413-wait-roster-pr1927.md
[29bf]: ../journal/2026/2026-10-29-raid-29bf18-gaze-close-and-deletion-path.md
[d225]: ../journal/2026/2026-10-30-raid-d2253c-gaze-seat-evidence.md
[vel]: ../journal/2026/2026-10-21-velocity-raid-1167-1169.md
[eve]: ../journal/2026/2026-10-26-evening-review-ceremony.md
[1302]: ../journal/2026/2026-10-28-raid-1302-1306-wrapup.md
[1634]: ../journal/2026/2026-10-23-review-merge-1634-1635.md
[fold]: ../journal/2026/2026-10-21-gate-on-folds-and-wall-down.md
[1366]: ../journal/2026/2026-10-30-gate-record-lost-shared-ref-rewind-1366.md
[hunt]: ../journal/2026/2026-10-27-hunt-phases-1235-override-merge.md
[prem]: ../journal/2026/2026-10-29-ready-ticket-review-premise-check.md
[cat]: ../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md
[xfam]: ../journal/2026/2026-10-31-cross-family-gate-dropped.md
[bdf7]: ../journal/2026/2026-11-01-raid-bdf7dd-2fb774-seat-parsing.md
[f3ac]: ../journal/2026/2026-10-31-raid-f3ac96-seat-identity.md
[2102]: ../journal/2026/2026-10-31-t1396-seat-forgery-regression.md
[3d5ae7]: ../journal/2026/2026-10-31-raid-3d5ae7-skill-case-notes.md
[dd72]: ../journal/2026/2026-10-31-raid-dd72df-t1402.md
[late]: ../journal/2026/2026-11-01-raid-1f0534-late-merges.md
[filing]: ../journal/2026/2026-11-05-pr2223-filing-pr-ticket-line-parsed-as-close-claim.md
[carry]: ../journal/2026/2026-10-30-raid-0da24b-scrub-fields-and-review-carry-over.md
[train]: ../journal/2026/2026-11-07-raid-train-controls.md
[morn]: ../journal/2026/2026-11-10-roar-morning-landings-1369-1417-1465-1504-1505-1506.md
[2351]: ../journal/2026/2026-11-09-roar-pr2351-government-cooldown-review.md
[829e]: ../journal/2026/2026-11-09-raid-829e9e-native-store-prune.md
[2402]: ../journal/2026/2026-11-10-roar-pr2402-codex-reader-raid-3429da.md
[3429]: ../journal/2026/2026-11-10-roar-pr2407-pi-reader-raid-626455.md
[45e1]: ../journal/2026/2026-11-10-roar-raid-45e130-fleet-audit-trace-runtimes.md
[1479]: ../journal/2026/2026-11-09-raid-1479-pin-moved-during-gate.md
[88e7]: ../journal/2026/2026-11-09-raid-88e70d-blind-spot-exit-check.md
[632b]: ../journal/2026/2026-11-09-raid-632b19-wave2-projects-untrack.md
[1488]: ../journal/2026/2026-11-09-raid-1488-single-ticket.md
[4afd]: ../journal/2026/2026-11-09-raid-4afdb3-post-skill-gaze-close.md
[91a3]: ../journal/2026/2026-11-10-raid-91a35c.md
[13f6]: ../journal/2026/2026-11-10-roar-raid-13f6d8-zotero-attach-licence-and-embedded-title.md
[2378]: ../journal/2026/2026-11-10-roar-pr2378-reach-tail-raid-6ee79f.md
[ce1c]: ../journal/2026/2026-11-10-roar-raid-ce1c5a-raid-land-nested-worktree.md
[f7aa]: ../journal/2026/2026-11-10-raid-f7aac3-staging-recognition-and-receipts.md
[1495]: ../journal/2026/2026-11-09-roar-1495-gc-reclaim-third-round.md
[a8b3]: ../journal/2026/2026-11-09-roar-raid-a8b3e4-gate-cleanup-and-publist.md
[2442]: ../journal/2026/2026-11-10-pr2442-gate-needs-author-on-conversation-ruling.md
[5c2a]: ../journal/2026/2026-11-09-roar-raid-5c2a37-landing-and-doudou-control.md
[2397]: ../journal/2026/2026-11-10-roar-pr2397-audit-names-runtimes-read.md
[1483]: ../journal/2026/2026-11-09-raid-1483-paper-skill.md
[2365]: ../journal/2026/2026-11-10-roar-pr2365-context-length-design-note.md
[61f5]: ../journal/2026/2026-11-10-raid-61f50c.md

Also examined, no claim kept: [1390 evidence](../journal/2026/2026-10-14-pr1390-review-evidence.md), [healthcheck](../journal/2026/2026-10-15-morning-healthcheck-merges-ticket-revalidation.md), [1456](../journal/2026/2026-10-19-pr1456-review-and-attribution.md), [1150](../journal/2026/2026-10-20-raid-1150-and-1146-integration.md), [1153 stack](../journal/2026/2026-10-21-1153-stack-landed.md), [waits](../journal/2026/2026-10-21-await-external-probes.md), [1170](../journal/2026/2026-10-21-raid-1170-1173-1175.md), [stack](../journal/2026/2026-10-21-raid-stack-and-merge-helper.md), [1212](../journal/2026/2026-10-26-raid-1212-1211-1221-1219-1220-1215.md), [capture-pr](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md), [1732](../journal/2026/2026-10-27-erg-sync-molt-step-1732.md), [1214](../journal/2026/2026-10-27-raid-1214-1218-waiting-follies.md), [1841](../journal/2026/2026-10-27-roar-1841-watchlist-closures.md), [run-pool](../journal/2026/2026-10-31-t1396-run-pool-throttle.md), [wrapup](../journal/2026/2026-11-01-raid-1f0534-wrapup.md), [wave 3](../journal/2026/2026-11-01-raid-1f0534-wave3-pi-agents.md), [1307](../journal/2026/2026-10-28-raid-1307-1308-pr1874-pr1876.md), [1136](../journal/2026/2026-10-20-raid-1136-1137-1126-and-1100-split.md), [1309](../journal/2026/2026-10-29-tracker-1309-closed.md), [t1396](../journal/2026/2026-10-31-t1396-session-identity-leak.md), [t1381](../journal/2026/2026-10-31-t1381-result-names-checks.md), [identity](../journal/2026/2026-11-05-pr2217-attribution-capture.md), [1485](../journal/2026/2026-11-09-1485-mission-skill-hunt.md), [fc10](../journal/2026/2026-11-10-raid-fc1083-doifetch-pin-v0-3-0.md), [2418](../journal/2026/2026-11-10-roar-pr2418-zotero-statements-ticket-1514.md), [075f](../journal/2026/2026-11-10-roar-raid-075fa8-one-roots-definition.md).
Previous page's 2026-10-02 to 10-15 episodes are in git: `git show HEAD:memory/topics/raid-review-and-merge.md`.

[source1]: user-rulings.md

## Fallback
