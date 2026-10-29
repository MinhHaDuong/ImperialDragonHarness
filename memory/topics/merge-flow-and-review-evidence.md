# Merge flow and review evidence (2026-10-19 to 2026-10-29)

Scope: how the merge path, the review battery and its evidence changed on
this repository after the fourth hoard, and what the changes produced. The
earlier period (forge checks, `erg-pr-merge`, the 15-file breaker, PR-comment
evidence) stays in [raids, review panels and merges](raid-review-and-merge.md)
as history. Procedures live in the `merge`, `gaze`, `verify-gate`, `raid` and
`hunt` skills; the doctrine lives in `rules/workflow.md` § Trust, Verify,
Monitor and § Escalation protocol. Nothing here amends them.

## Supported observations: the merge path

Local merge gate. Tracker 1045 went live with PR 1569 (2026-10-21): every merge
needs a gate record on the exact merge candidate, and any merge into `main`,
including the helper's own ticket-close commit, stales it. `scripts/main_sweep.py`
(1179, PR 1610) audits the last 24 h for commits without a receipt; before it
merged, two seats reproduced four ways past the hook or audit. The same day the
15-file wall was removed (PR 1614), 1045 closed with 1180 as its own gate
(PR 1625), `review-pr` folded into gaze (1144, PRs 1607-1609) and the
`erg-pr-merge`/`erg-pr-status` helpers were deleted (1178, PRs 1617-1619)
([gate on folds](../journal/2026/2026-10-21-gate-on-folds-and-wall-down.md)).
Before the wall fell, it forced splits: 1129's PR into #1495/#1488, #1489 into
three, and the gaze-shrink stack re-sliced by criterion into #1538-#1540
([1153 stack](../journal/2026/2026-10-21-1153-stack-landed.md)).

Optimistic merge. Tracker 1226 (rewritten after PR #1676 was parked) landed on
2026-10-27: a before-merge gate of about 13 s (1245), the full suite after the
merge (`merge-gate.py run-after`, 1244), a red after-merge run opening a ticket
(1251), landing through `scripts/raid_land.py` (1255), and the runner started
from `hooks/reference-transaction` (1265)
([afternoon raid](../journal/2026/2026-10-27-raid-optimistic-merge-afternoon.md)).
After-merge reds 1295 and 1322 were closed on later green records without an
isolated cause; the gate record keeps test ids, not failure text
([1322](../journal/2026/2026-10-28-after-merge-red-1322-cleared.md)). Main went
red after #1799 because callers outside the moved set ran in no review or gate;
fixed forward in #1811
([forge-less raid](../journal/2026/2026-10-27-raid-forge-less-and-guard.md)).

Gate-record staleness recurred whenever another session merged during the
record (PR 1703 twice, #1720, PR 1725 twice, #1885). On PR 1725 the author said
"Just merge, dont rerun the tests" and it merged pinned to its head with no
record on the final candidate, the bypass logged in a PR comment
([sitrep 1246](../journal/2026/2026-10-27-raid-sitrep-ticket-1246.md)). After a
conflict resolution `merge-gate.py tier --since <ruled tip>` answers `full`, so
each sibling conflict cost one narrow gaze
([runtime verbs](../journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md)).
The orchestrator skipped `/merge` step 8 for the first 13 merges of one raid and
helpers ran from a stale primary checkout; no after-merge runner started for 15
merges until one was run by hand (afternoon raid).

A hand ticket close following `skills/merge/references/claims.md` § Repair
staged only the deletion, because `erg close` had already moved the file;
`git show --stat` caught it before the gate. `raid_land.py` stages both sides
([erg close](../journal/2026/2026-10-28-erg-close-hand-recipe-dropped-ticket.md)).

## Supported observations: review evidence on notes

Tracker 1298 moved gaze, verify-gate and attribution evidence to local git
notes. Author ruling: "independence first; notes local, background push, sync
at PR merge" ([F1 gap](../journal/2026/2026-10-28-readme-pr1853-f1-notes-gap.md));
earlier ruling (ticket 1277): "F1 default (notes review + forge PR merge); F2
(local gated merge) only with no origin remote; no setting." Measured on padme:
`gh pr view` about 0.5 s, notes fetch 0.4-0.5 s, local `git notes show` about
0.00 s. Children 1299-1301 each fixed a defect of the transport (a fetch refspec
breaking plain `git fetch`, split round-1 verdicts from two clones, a `gh`
timeout) ([1298 raid](../journal/2026/2026-10-28-raid-1298-f1-notes-evidence.md)).
Ticket 1305: 7 of 15 gate runs refused REVIEWED diffs because gaze inferred
`scope: delta` from any intent; the author ruled the label a guard on a guard
and it was deleted ([gate scope](../journal/2026/2026-10-28-gate-scope-and-doctor-kit.md)).

Cross-family seats. Ticket 1326 assumed a nested gaze could not reach a codex
seat; reproduction showed `gaze_seat.py launch --runtime codex` working at depth
1 and 2, and five notes answers carried self-written "no cross-family seat"
reasons although the host consents to OpenAI and Mistral. The lost seat was an
opt-out, not a refusal; the gate now takes `--require-cross-family`
([1326](../journal/2026/2026-10-28-raid-f642df-1326-opt-out-not-refusal.md)).
Gaze run from nested subagents returned `seats: self-only` repeatedly (#1915
three times, five wave-1 runs, #1897, #1899, #1927, 1967, 1970); explicit panel
briefs or a re-run fixed it. Detached runners posted `seats: panel` without the
cross-family seat in 2 of 7 runs; both were voided and rerun
([raid b](../journal/2026/2026-10-27-raid-b-followups.md)). On #1862 and #1927
the codex seat found blocking defects the self-only pass had missed
([1303](../journal/2026/2026-10-28-raid-1303-pr1862.md),
[wait roster](../journal/2026/2026-10-28-raid-534413-wait-roster-pr1927.md)).

Verify-gate admission. It refuses without spending a round when `repo=` is
missing (17 of 103 launches since 2026-10-21, the entry's trace count), when the
head moved after gaze, or when only a delta answer covers the head. It returned
NEEDS-AUTHOR when decisions rested on agent-written lines indistinguishable from
the author under the shared account (PR 1690, PR 1841), and ESCALATE on PR 1722
because "an author instruction relayed by an agent is not approval"
([gate flows](../journal/2026/2026-10-28-review-gate-flows-pr1863.md),
[PR 1945](../journal/2026/2026-10-29-doc-propagation-pr1945.md)). PR #1863
resolved a contradiction between raid Phase 7 ("revert last merge") and merge
step 9 (a red is reported, never reverted) on option A.

## Supported observations: round counts and the stopping bar

Long review loops: PR #1676 thirteen gaze rounds, then "Parked. Human review
needed to redesign the solution."
([review cost](../journal/2026/2026-10-27-review-cost-raid-and-redesign.md));
PRs 1638 and 1640 five rounds each, the 1640 concurrency machinery removed as
"theoretical" ([worktree GC](../journal/2026/2026-10-23-worktree-gc-ownerless-locks-1638-1640.md));
PR 1622 five FINDINGS rounds, then the author's `--force-approve`
([contradiction sweep](../journal/2026/2026-10-21-instruction-contradiction-sweep-pr1622.md));
PR #1704 four rounds, then "ENOUGH" and an override merge
([hunt phases](../journal/2026/2026-10-27-hunt-phases-1235-override-merge.md));
#1941 five rounds, each authorized past the breaker
([doctor triage](../journal/2026/2026-10-29-harness-doctor-triage.md)). The
gaze-shrink union took five cross-family reads before a stopping rule: "stop
when a round finds no defect that is both absent on main and over the severity
floor" (1153 stack). PR #1847 then fixed the bar in the finding schema: a
blocking or verifiable finding carries `scenario:` and `on main:`, the bar is
the same every round, and fresh blockers at round 3 mean a redesign
([diminishing returns](../journal/2026/2026-10-28-diminishing-returns-bar.md)).

Cost datapoints: gaze median 178 s over 112 runs (setup 22%, panel 57%,
closing 21%); ticket 1227 priced about 60 s saved per run and delivered about
2 s ([test-doctor](../journal/2026/2026-10-29-test-doctor-gate-contention.md)).

## Author decisions recorded in the sources

"We are KISSing the review system with a Trust, Verify, Monitor doctrine"
([raid 1170](../journal/2026/2026-10-21-raid-1170-1173-1175.md)); "Stay
optimistic. Trust, Verify, Monitor." (afternoon raid). The doctrine and the
escalation protocol entered `rules/workflow.md` through PR 1778
([doctrine](../journal/2026/2026-10-27-doctrine-escalation-pr1778.md)); memory
records provenance only. "PRs are not waiting points; the existing ticket
carries the follow-up" ([1466](../journal/2026/2026-10-19-smart-testing-1466-wrap-up.md)).
Waivers in the author's own words: "Waive it, merge 1559"
([velocity raid](../journal/2026/2026-10-21-velocity-raid-1167-1169.md)), PR 1633
"merge" ([1633](../journal/2026/2026-10-26-pr1633-merge-on-author-authority.md)),
PR 1744 "no ceremony" ([docs move](../journal/2026/2026-10-27-docs-to-conception-pr1744.md)).
A waiver relayed by an agent was refused by gaze on #1447 until the author wrote
it ([verbs](../journal/2026/2026-10-16-zotero-verbs-exact-match.md)).

## Review-attribution records

This pass examined 98 further `review-attribution` records, for PRs #1415 to
#1970 (2026-10-15 to 2026-10-29), ledgered in the
[fifth hoard](../hoards/2026-10-29-fifth-hoard.md). Counts were derived by the
helpers with `grep`, not measured by the capture flow. Through 2026-10-26 most
reviewer lines are `runtime-masked` (Claude Code subagent seats expose no
verbatim model id). The 2026-10-26 records for #1656-#1667 take Claude ids from
subagent transcript `model` fields and add the provider prefix "as in the
existing records"; the raid entry of the same day had called their capture
failed. The 42 records of 2026-10-28/29 hold 148 reviewer lines (141 ran,
7 failed) and 135 findings (55 adopted); cross-family coverage came almost only
from codex seats (`openai/gpt-6.1-sol`, `openai/gpt-6-luna`). Same-family or
reused-context panels are labelled as such in many records; no record is
treated here as an independent sample beyond what it states.

Capture friction recurred: no record for many PRs of 2026-10-19 to 2026-10-21
(the author "decided to leave the gap" for raid 1136); grammar refusals
(`fact order requires kind, pr, writer before reviewers`, non-qualified ids,
`nit`, `other-family`, duplicate findings in one attempt); `gh pr edit` body
rewrites deleting blocks (1623, 1638). `--capture-pr` (PR #1719) made capture
one call; at /roar for PR 1722 the author said to skip attribution ("it is
broken"), and ruled no retrospective capture for blocks predating the 1286 fix
([held tickets](../journal/2026/2026-10-27-session-close-held-tickets.md)).
Ticket 1243 (record in the merge commit) is closed; the attribution backfill
appended zero in every run, unresolved count rising 76 → 91 → 92 → 101.

## Hypotheses, not facts

That nested launches lose the cross-family seat because of the brief, not the
runtime, rests on 1326's reproduction and the reruns; no controlled comparison
ran. That the stopping bar shortened loops is not measured.

## Sources

- The entries linked above, plus [catalog grouping](../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md), [merge inspection 1117](../journal/2026/2026-10-19-merge-inspection-1117.md), [raid 1136](../journal/2026/2026-10-20-raid-1136-1137-1126-and-1100-split.md), [raid 1150](../journal/2026/2026-10-20-raid-1150-and-1146-integration.md), [evening ceremony](../journal/2026/2026-10-26-evening-review-ceremony.md), [capture-pr](../journal/2026/2026-10-27-capture-pr-and-merge-commit-attribution.md), [forge leaks](../journal/2026/2026-10-28-raid-f7fa41-forge-leaks.md), [raid 1307/1308](../journal/2026/2026-10-28-raid-1307-1308-pr1874-pr1876.md), [resident budget](../journal/2026/2026-10-29-raid-6958fe-resident-budget-composition.md).
- Records: `memory/journal/2026/2026-10-{15..29}-review-attribution-pr*.md`, ledgered in the fifth hoard.
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
