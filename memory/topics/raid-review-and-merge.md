# Raids, review panels and merges

Scope: what the raid, gaze and merge flows produced on this repository from
2026-10-02 to 2026-10-07: which layer caught which defect, how panels
degraded, how overrides were used, and what the review-attribution records
hold. The procedures themselves live in the `raid`, `gaze`, `verify-gate` and
`merge` skills; nothing here amends them.

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

## Supported observations: degraded panels

Spawn results were not reliable. A runtime's silent subagent cap returned
`success` for seats that never registered; the pre-written roster exposed four
missing seats (raid 1008). A docprop seat never reported despite a successful
spawn (PR #1143, ticket 1021). Executors without an Agent tool (pi, Vibe
child sessions, the 0875 hunt executor) posted `PANEL-INTEGRITY: DEGRADED`;
detached headless CLI seats, one process per seat with artifact polling,
restored full panels from 2026-10-02 onward (ticket 1017), except that
detached `vibe -p` seats were blocked by the runtime's approval policy. In every
entry that mentions it, the openrouter-budget seat failed fail-open (the
ticket 0347 hang class) while the openrouter-frontier seat ran.

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

On 2026-10-03 the author stated, for tracker 0205, that "a purely
administrative tracker can go when there is only one operational task left.
In fact the tracker should be the crowning delivery task." The entry records
that this was applied but written into no rules file; it is an author
statement, not a rule held by memory.

## Review-attribution records

The journal holds 33 `kind: review-attribution` records for PRs merged
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

## Hypotheses, not facts

The pairing "gates prove what is tested; panels catch what the prose promises
and the code does not do" is the 2026-10-04 entry's reading of one artifact.
The episodes above are consistent with it, but no comparison of catch rates
was run.

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
- [Reviewer attribution design](../journal/2026/2026-10-02-reviewer-attribution-design.md) — processed by the first dream; linked here as the design behind the records.
- The 33 records: `memory/journal/2026/2026-10-0[56]-review-attribution-pr*.md`, ledgered in the [2026-10-07 dream](../dreams/2026-10-07-second-dream.md).
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
