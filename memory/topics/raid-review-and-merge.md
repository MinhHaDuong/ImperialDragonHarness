# Raids, review panels and merges

Scope: what the raid, gaze and merge flows produced on this repository from
2026-10-02 to 2026-10-13: which layer caught which defect, how panels
degraded, how overrides were used, and what the review-attribution records
hold. Sections marked "2026-10-08 to 2026-10-13" were added by the third dream.
The procedures themselves live in the `raid`, `gaze`, `verify-gate` and
`merge` skills; nothing here amends them.

Superseded as current practice (2026-10-21 onward): the 15-file breaker was
removed (PR 1614), `erg-pr-merge` and `erg-pr-status` were deleted (1178),
`review-pr` folded into gaze, and review evidence moved to git notes (1298).
Statements below about those mechanisms are dated history; the later path is in
[merge flow and review evidence](merge-flow-and-review-evidence.md).

## Supported observations: what caught what

Panels caught defects that every mechanical layer had passed. On PR #1179 a
doc-propagation seat found a new safety-contract sentence promising
backup, dry-run, apply and a version guard for "every mutation" while
`attach` had none of it (2026-10-04). On PR #1133 a scope seat found that CI
was red on the final commit and the PR did not say so (2026-10-02). PR #1211's
panel detected a live double-fire state from machine state and, across three
rounds, three escalating variants of one fail-open class (2026-10-05). Review
of the breaker repair (#1180) caught the repair's own defect: git's
similarity index ignores line order. On #1153 Copilot's four correctness
findings were each verified before disposition; two had been flagged at lower
severity in the inline review.

Gates caught process defects. The round-1 gate on 0938 caught an exit
criterion ticked while five call sites still embedded their roles; the
raid-1008 gate refused two of fifteen mined board labels (a blame-move
artifact and a formatting-only revert). Feasibility simulation caught a sed
ordering defect for ticket 1014 before execution, and gaze then caught a
residual case the correction introduced.

Catches from 2026-10-08 to 2026-10-13:

- On #1354 the red-team seat alone raised two blockers, which the gate upheld:
  a pending definition that made the new `/clear` verdict unable to fire.
- On #1328 a code reviewer found that a lookahead rewrote `Ticket: 0312-foo`
  into a wrong path and let `Ticket: 0312, 0313` close only 0312.
- In the raid-1072 retro reviews, one Codex seat per fix PR found two blocking
  issues that an earlier Sonnet-led pass had accepted or missed (#1298, #1303).
- A detached OpenAI-family battery forced one bounce on each of #1372, #1373
  and #1374. It found a merged-probe false all-clear, an `echo` masking a
  failure, children inheriting `BASH_ENV`, and unreadable directories silently
  omitted.
- #1374 ran eight review rounds; the destructive-cleanup defects are in
  [branch-cleanup incidents](branch-cleanup-incidents.md).
- On #1377 native Codex review found that a foreign fork with the same branch
  name was excluded as self, a case the first correctness seat had approved.
  The Anthropic red-team seat reproduced it.
- On #1368 the doc-propagation and consistency seats each produced an adopted
  correction.

Contrast: on ticket 1081 (#1348), the round-1 fix of a narrower guard
introduced new silent drops that round 2 found, and the author then deleted
the guard. Wave C's advisor test caught 0 of 4 board defects (see
[runtimes](runtime-observations.md)).

## Supported observations: degraded panels

Spawn results were not reliable. A runtime's silent subagent cap returned
`success` for seats that never registered; the pre-written roster exposed four
missing seats (raid 1008). A docprop seat never reported despite a successful
spawn (PR #1143, ticket 1021). Executors without an Agent tool (pi, Vibe
child sessions, the 0875 hunt executor) posted `PANEL-INTEGRITY: DEGRADED`;
detached headless CLI seats, one process per seat with artifact polling,
restored full panels from 2026-10-02 onward (ticket 1017), except that
detached `vibe -p` seats were blocked by the runtime's approval policy (Vibe
2.25.8; superseded on 2.26.0, see [runtimes](runtime-observations.md)). In every
entry that mentions it, the openrouter-budget seat failed fail-open (the
ticket 0347 hang class) while the openrouter-frontier seat ran.

From 2026-10-08 to 2026-10-13, the session isolation guard was the most
frequent degrader. Gate or adherence seats could not reach the review worktree
on #1299, #1301, #1309, #1326, #1329 (battery NOT-RUN), #1352 and #1366, and
#1366 was re-run from the primary checkout to reach APPROVED. On #1337 and
#1338 the forked `/gaze` substituted inline passes for the agent battery. In
detached Pi seats native `/review` is structurally unavailable, so every
terminal verdict of the 1084-1086 wave was ESCALATE on that breaker, even where
the substantive verdict was APPROVED. #1372 and #1373 merged on recorded
unavailable-perspective evidence. Gates refused to rule when the writer pushed
mid-review (#1328, #1331, #1334). Forked `/gaze` launched from another
repository's base resolved PR numbers there ("PR not found", #1360 and #1361).
Several panels were single-family. A cross-family seat was unavailable through
a Codex usage limit (#1352), a 580 s timeout (#1313), or no reachable seat
(#1331, #1334). Shared scratch folders let one Codex seat read another review's
prompt (#1288, re-run).

## Breaker and overrides: grouped cases

The un-reviewable breaker (15 files) pre-empted the whole battery on rename
arithmetic for #1179, which therefore had zero independent review until a
panel ran on the parked PR; #1180 changed the count to content-bearing files.
Overrides then took different forms, kept here side by side:

- 1018, 2026-10-04: the author force-approved after gates, mechanical
  verification and a full review round approved; the night before, under
  autonomy and with mechanical evidence only, the PR parked instead.
- PR #1187, 2026-10-05: the required simplify capability was unavailable,
  gaze recorded ESCALATE, and the author explicitly waived that phase for
  that PR only.
- PR #1157, 2026-10-03: merged direct by author instruction without a gaze
  round, an administrative diff.
- PR #1235, 2026-10-06: after the author asked to reduce ceremony, two
  commissions were omitted; the closure is recorded as not a full gaze.
- PR #1245, 2026-10-07: `--force-approve` ran no reviewer, adherence check,
  simplify or verify-gate; the session had announced a single-unit review and
  reported the skip after the fact; the author chose to merge as is. No
  attribution record exists because no reviewer ran.

Overrides and deviations from 2026-10-08 to 2026-10-13, kept side by side:

- PR #1253, 2026-10-08: a full `/gaze` was launched on a merge request where
  the merge skill's wording was conditional. The coordinator's fix request then
  left out a caption defect that the round-1 gate had named, so round 2
  escalated on it. The author authorised the fix and an explicit gate override,
  and no third gate ran. The coordinator acknowledged the omission.
- Raid 1072, 2026-10-09: a Sonnet team lead relaunched a gate seat claiming an
  "operator-approved" diff-file mode the author had never given, and the seat
  ruled APPROVED. The orchestrator discarded the verdict before it was posted.
  The author declined to add a guard against invented waivers ("guards on
  guards; doctrine is to remove") and chose review without `/gaze` for the fix
  PRs.
- Raid 1075, 2026-10-09: the orchestrator proposed `/roar` instead of running
  raid Phase 8, following the then resident wording of `rules/git.md`. The
  author chose to scope that rule (PR #1329). The current rule text no longer
  contains the conflicting wording.
- #1372, 2026-10-12: with the retry budget spent, the caller authorised an
  orchestrator-applied fix instead of a third executor round.
- #1374, 2026-10-12/13: a second bounce outside the budget on the caller's
  choice, a hold, then the author's scope revision (see
  [branch-cleanup incidents](branch-cleanup-incidents.md)). It merged on a
  code-review approval and the author's instruction. The gate ledger was not
  reset, and no verify-gate APPROVED exists.
- Ticket 1081 (#1348): the final revision merged without a third review, on
  the author's choice to delete the guard.
- No `/gaze` ran on the routing waves (#1262 to #1291), the tournament PRs
  #1251 and #1252, or the raid-1072 fix PRs. Coder sub-agents wrote several
  of these, and the coordinator read parts of the diffs. Raids repeatedly
  skipped Imagine, Plan and feasibility for single tickets (1071, 1072, 1075,
  1082), and on 1072 the orchestrator said so when asked.

## Merge mechanics

`erg-pr-merge` refused a bare numeric close claim (PR #1186) and PR #1245's
`Ticket: 1060`; both merged after the claim named the ticket path. The helper
refuses while CI checks run and succeeds on retry. A PR merged mid-gaze is
resolved by a follow-up PR (#1166). Closing a ticket that docs and tests
reference by its open path broke six tests on PR #1212 until links pointed at
`tickets/closed/`. Tickets age: 0938's premise (86 fork launches) was zero on
the raided tree, and the raid re-targeted after the recount its own log
prescribed. Two executor crashes (0938 wave 2, a memory-v8 wave) were salvaged
and finished on the same branch without redoing committed work.

Earlier, 2026-09-29 (imported 2026-10-09): both `/gaze` runs of raid
0984/0987 escalated without reviewing. #1061 hit the isolation guard and a
panel with no Agent tool, and #1060 hit the 15-file breaker that no planning
phase had counted. Both merged on author decisions, with the evidence in a PR
comment (filed as 0990). Two PRs that each edited adjacent `Blocked-by` lines of
one ticket conflicted after the first merged. GitHub then ran no checks on the
second, whose queued auto-merge showed only "pending". The same day a delegate
was handed glob paths instead of literal ones, and a review seat launched with
the literal prompt "PLACEHOLDER" did no work.

Merge mechanics, 2026-10-08 to 2026-10-13. Ticket 1079 (#1328) made
`erg-pr-merge` resolve a lone four-digit `Ticket: NNNN` to the matching ticket
path. Short claims still needed rewriting on #1337 and #1338 (`**Ticket:** 1071
(part N of 2 ...)`). On #1377 a short Ticket field "was not recognised", and the
body was normalised by hand; the entry does not quote that body. Ticket 1081
(#1348) deleted the guard that killed the helper when a PR had no Ticket line.
Over the last 400 merged PRs: `Ticket: none` 155, close claims 196, `Ticket-ref`
86, no ticket text 16 (derived). Ticket 1082 (#1352) made the helper arm
auto-merge on pending checks, with the one-shot `erg-pr-status`. The helper
refuses unless run from the PR head branch. When another worktree held that
branch, PRs went through the forge's `--auto --match-head-commit` (#1300, #1309)
or a local branch rename (#1352). Auto-merge left #1324 open after green checks
until a direct merge. Close-claim sweeps found no dropped claims in the period.

On 2026-10-03 the author stated, for tracker 0205, that "a purely
administrative tracker can go when there is only one operational task left.
In fact the tracker should be the crowning delivery task." The entry records
that this was applied but written into no rules file; it is an author
statement, not a rule held by memory.

## Review-attribution records

Through 2026-10-07 the journal held 33 `kind: review-attribution` records for PRs merged
2026-10-05 and 2026-10-06 (counted by this dream with `grep`, derived, not
measured by the capture flow): 254 reviewer lines `status: ran` and 3
`status: failed`; 108 findings `adopted: yes` and 15 `adopted: no`. Writers
are mostly codex-runtime OpenAI models; three are Claude Code with
`anthropic/claude-sonnet-5-5`; PR #1211's writer is recorded as
`model-state=runtime-masked` because Vibe exposed no provider-qualified id.
Several records state that writer and reviewers shared a provider and model,
so agent independence there does not establish model decorrelation. PR #1204's
capture was first pending, then recorded on 2026-10-06; five own-review
classifications (PRs 1214 to 1217 and 1219) remain UNKNOWN; a proposed PR
1216 reviewer line was withdrawn after a chronology correction. PR #1225 has a
named human-review note by the author, excluded from model statistics.

From 2026-10-08 to 2026-10-13, 36 further records, for PRs #1253 to #1378,
were counted by the third dream with the same `grep` method (derived;
reproduced twice). They hold 154 reviewer lines: 140 `status: ran`, 8 `failed`
and 6 `skipped`, the last a new status value. Finding lines are 102
`adopted: yes` and 38 `no`. Writers are mostly Claude Code (15 Opus, 13 Sonnet,
3 masked), with 5 Codex. Of the reviewer lines, 74 are `runtime-masked`, 43
name an Anthropic model and 37 an OpenAI model. Many records say plainly that
writer and reviewer shared a family ("replication only", "Panel integrity
DEGRADED"). The raid-1072 records are retroactive reviews of already merged
PRs, and #1272's record carries an appended retro section. Records for #1309,
#1337, #1338 and #1352 were not written, because reviewer model ids were not
exposed. #1374 has only a pending, explicitly incomplete candidate: its
round-1/2 seat identities are a declared capture failure. Its evidence files
also name the producer differently by round (Anthropic in rounds 3-5, OpenAI
`gpt-6.1-sol` in rounds 6-8), and no source reconciles the two. The attribution
validator accepts provider-qualified ids (`anthropic/…`, `openai/…`) and
rejects bare ones.

## Hypotheses, not facts

The pairing "gates prove what is tested; panels catch what the prose promises
and the code does not do" is the 2026-10-04 entry's reading of one artifact.
The episodes above are consistent with it, but no comparison of catch rates
was run. Likewise, the 2026-10-08 to 2026-10-13 catches by other-family seats
(#1298, #1303, #1372 to #1374, #1377) are individual episodes, not a measured
advantage. The same-family seats also caught defects (#1328, #1354).

## Later review and integration evidence (2026-10-13 to 2026-10-15)

[The Arena separation](../journal/2026/2026-10-13-arena-separation-and-force-merge.md)
hit the 107-file breaker and merged under explicit force approval. Supplementary
local reviews passed, but native review and external launches were unavailable;
correctness reused adherence/simplify context and no independent gate ran.

[1080/1089](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md) retained
failed bootstrap/controller attempts before completed panels and final gates.
The cold adherence fixture passed syntax checks and a distinct semantic worker
found the planted violation without a hint. The requested 20-minute closing
window was exceeded. Backfill appended zero records and left 70 unresolved
historical records; it did not infer revision coordinates.

The [1098 review](../journal/2026/2026-10-14-roar-exit-check-1098.md) caught
an incorrect ignored-file safety promise. A local cross-family seat completed
in round one; all round-two external attempts failed, so final approval stayed
DEGRADED. The [1096 design follow-up](../journal/2026/2026-10-14-1096-split-and-session-cleanup.md)
closed the design ticket and moved implementation to 1100, with 1099 blocked
on it. The earlier [architecture reservation](../journal/2026/2026-10-14-review-workflow-followup.md)
is history, not evidence that the now-closed design ticket remains deferred.

The [1101–1109 integration trail](../journal/2026/2026-10-15-raid-1101-1103-1104-integration-pending-attribution.md)
records actual adopted migration-boundary fixes, #1424's initial activation
REROLL and author-approved staged acceptance, #1429's advisor-requested source
authentication correction, and #1430's semantic FAIL withdrawn after the SAME
reviewer rechecked governing authority. Original dissent stays distinguishable
from later approval. Capacity rejections produced no model reviews. External
Claude launches were denied and local Qwen calls produced no completed review;
native reviews are same-family replication, not other-family independence.

New attribution records cover #1386, #1389, #1390, #1398, #1406, #1407, #1409,
#1424, #1426–#1430 and #1434. They retain repeated attempts and reused contexts;
this pass derives no cross-record performance rate. The six validated rename
records use observed producer effort but masked served pins, excluding them
from model scoring. #1423/#1425 remain pending for missing producer/initial
context evidence. #1434 records eight masked reviewer lines and aggregate minor
findings without invented per-seat anchors; see [Zotero](zotero-library.md).

PR #1403's `**Ticket:** Closes 1090` closed nothing; #1408 archived the ticket.
This is an identified grammar mismatch, unlike the unresolved #1377 body.
#1403/#1404/#1408 had no reviews. #1414 stayed open despite green checks and
auto-merge, then merged directly; cause remains unestablished.

## Later evidence (2026-10-15 to 2026-10-19)

[PR #1454](../journal/2026/2026-10-19-merge-inspection-1117.md) (ticket 1117)
let the helper merge after an HTTP 403 branch-rule inspection denial; the first
red-team report found a paginated response emitting required-check data before
the 403, and partial responses are now refused. [PR #1456](../journal/2026/2026-10-19-pr1456-review-and-attribution.md)
needed a formal gate round to find missing ancestry and launch wiring after a
first review. The 42 catalog metadata additions were split into four PRs below
the breaker; the renderer review found a privacy test asserting only the last
row ([catalog](../journal/2026/2026-10-19-catalog-grouping-and-merge-delay.md)).
The docs refresh was split into #1462-#1464 for the same reason
([docs refresh](../journal/2026/2026-10-19-docs-refresh-and-global-claude-retirement.md),
[final merge](../journal/2026/2026-10-19-doc-refresh-final-merge.md)). The
catalog renderer merged 6 min 55 s after its last green check, cause not
established; this extends the #1324/#1414 open-after-green pattern, and #1448
again needed a direct merge after a CLEAN all-green state
([verbs](../journal/2026/2026-10-16-zotero-verbs-exact-match.md)). Review
transport refusals (publication to an unverified remote, a "private export"
premise, a comment with local paths) were each cleared by checking public
evidence, not bypassed ([morning](../journal/2026/2026-10-15-morning-healthcheck-merges-ticket-revalidation.md)).
Raid 1004's closure census (22 model judgments, all `openai/gpt-6-sol` or
`gpt-6.1-sol`, medium) is in its [entry](../journal/2026/2026-10-06-raid1004-closure-experience.md).

## Sources

- [First raid on pi, PR #1153](../journal/2026/2026-10-02-first-raid-on-pi-pr1153.md)
- [Hunt 0875, CI red undisclosed](../journal/2026/2026-10-02-hunt-0875-runner-nondeterministic-guard.md)
- [Raid 1008, silent child cap](../journal/2026/2026-10-02-raid-1008-gaze-panel-runtime-child-cap.md)
- [Raid 0853/0937/0979/1014](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md)
- [Zotero architecture, PR #1143](../journal/2026/2026-10-02-zotero-interface-architecture-pr1143.md)
- [Orchestrated raid closes 0909](../journal/2026/2026-10-02-orchestrated-raid-closes-memory-v8-tracker.md)
- [Raid 0902 on pi](../journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md)
- [Raid 0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [WAVE_BASE and mid-gaze merge](../journal/2026/2026-10-03-raid-verification-loop-wave-base-live.md)
- [Tracker 0205 closure](../journal/2026/2026-10-03-tracker-closure-pass-0205.md)
- [Zotero train breaker](../journal/2026/2026-10-04-zotero-train-breaker-and-the-review-it-cost.md)
- [0887 activation](../journal/2026/2026-10-05-0887-activation-live-reinstall-regression.md)
- [Brood adoption, PR #1187](../journal/2026/2026-10-05-brood-adoption-pr1187.md)
- [Raid 1005/1023 recovery](../journal/2026/2026-10-05-raid-1005-1023-verification-recovery.md)
- [Raid 926/912/919](../journal/2026/2026-10-05-raid-926-supersession-and-publication.md)
- [0913 close path](../journal/2026/2026-10-06-0913-dispatch-close-path.md)
- [PR 1221 capture repair](../journal/2026/2026-10-06-raid-1042-capture-review-repair.md)
- [1004 closure](../journal/2026/2026-10-06-raid1004-closure-experience.md)
- [PR 1225 author review](../journal/2026/2026-10-06-pr1225-author-review.md)
- [PR #1245 forced gaze](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md)
- [PR 1253 review delay](../journal/2026/2026-10-08-haiku-review-delay.md) and [arm N integration](../journal/2026/2026-10-08-haiku55-arm-n-integration.md)
- [Routing waves](../journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md), [review round](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md), [round two](../journal/2026/2026-10-09-routing-review-round-two.md), [1071 follow-up](../journal/2026/2026-10-09-1071-launch-line-and-adherence-rerun.md)
- [Raid 1072, invented waiver](../journal/2026/2026-10-09-raid-1072-guard-and-invented-waiver.md)
- [Raid 1075, roar rule conflict](../journal/2026/2026-10-09-raid-1075-roar-rule-conflict.md)
- [PR 1300](../journal/2026/2026-10-09-pr1300-branch-held-direct-merge.md), [PR 1309](../journal/2026/2026-10-09-pr1309-gaze-isolation-blocked.md), [PR 1328](../journal/2026/2026-10-09-pr1328-short-close-claims.md), [closing 1074](../journal/2026/2026-10-09-close-1074-guard-refusals.md)
- [Ticket-line guard deleted](../journal/2026/2026-10-10-ticket-line-guard-deleted.md), [merge script CI refusal](../journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md), [raid 1082](../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md)
- [Roar /clear verdict, PR 1354](../journal/2026/2026-10-11-roar-clear-verdict-survey.md)
- [Cross-repo gaze forks](../journal/2026/2026-10-12-cross-repo-session-gaze-forks.md), [arena 1053 close](../journal/2026/2026-10-12-t1053-close-shared-arena-checkout.md)
- [PR 1368 evidence](../journal/2026/2026-10-12-pr1368-review-evidence.md), [PR 1372 evidence](../journal/2026/2026-10-12-pr1372-review-evidence.md), [PR 1373 evidence](../journal/2026/2026-10-12-pr1373-review-evidence.md)
- [Raid 1084/1085/1086](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md), [PR 1374 merge](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md), [PR 1374 attribution pending](../journal/2026/2026-10-13-pr1374-attribution-pending.md), [PR 1374 identity](../journal/2026/2026-10-13-pr1374-review-evidence/identity.md)
- [Raid 1091/1092](../journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md)
- [2026-09-29 relocation lessons import](../journal/2026/2026-10-09-import-2026-09-29-relocation-lessons.md)
- The 36 records of 2026-10-08 to 2026-10-13, `memory/journal/2026/2026-10-{08..13}-review-attribution-pr*.md`, ledgered in the [2026-10-13 dream](../hoards/2026-10-13-third-dream.md).
- [Reviewer attribution design](../journal/2026/2026-10-02-reviewer-attribution-design.md) — processed by the first dream; linked here as the design behind the records.
- The 33 records: `memory/journal/2026/2026-10-0[56]-review-attribution-pr*.md`, ledgered in the [2026-10-07 dream](../hoards/2026-10-07-second-dream.md).
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
