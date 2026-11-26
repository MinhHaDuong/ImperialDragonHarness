# Execution evidence contract: ticket 1566

Date: 2026-11-26. This documentation repair supersedes the boundary-only
execution exception preserved during ticket 1565. It separates inspected
provision, boundary uncertainty, and observed numerical reproduction without
changing whole-paper execution scope, the selected main-result ACRe criteria,
numerical tolerance, adaptation policy, or the replication objectives.

## Contract walkthrough and evidence

Boundary evidence remains in `raw_analysis_boundary`, with unresolved
status and its inspected facts. It supplies no numerical execution category.
Raw and analysis execution are derived separately from their comparison
rows and the declared whole-paper inventory. A verified analysis-only
package can still support No for the raw row, but its evidence explicitly
says provision-based impossibility, rather than observed failure. It does
not establish `crr_echouee` without the main-result run evidence.

[checks.json](checks.json) records independently constructed synthetic
inputs to the **existing unchanged comparator**. They stipulate comparison
statuses for contract checks; no package generated those observations and
no second evaluator was written. Every dossier partitions the same complete
grid criterion set used by the supplied source controls. The following
contract-expected readings are manual walkthroughs of the revised text,
separate from the artifact's actual old-comparator results.

For the observed-comparison cases, the stipulated complete whole-paper
inventory requires `crr:p.estimate` and `crr:p.se`; both source paths are
identified as raw under a resolved documented boundary. The complete case
stipulates both match at the existing printed-digit tolerance. These are
synthetic control facts, not newly measured scientific coefficients.

| Independent control | Evidence and actual unchanged comparator output | Revised contract-expected reading |
|---|---|---|
| Boundary without a run | Inspected assembled panel and recodes; unresolved upstream boundary; empty execution coverage and comparison rows. The legacy dossier records the old ambiguity-only raw partial criterion. Actual raw execution: Partially | Not yet assessed; preserve the panel, recodes, boundary, and unknown coverage. Neither ambiguity nor the historical criterion supplies a numerical match or failed run |
| Observed partial | Complete required inventory; estimate matches and SE differs; actual raw execution: Partially | Partially on observed comparisons; cite both outcome rows and their scope |
| Complete match | Same complete required inventory; estimate and SE both match; actual raw execution: Fully | Fully on observed comparisons; a main-result-only subset could not establish this for the whole paper |
| Observed failure | Same complete inventory; estimate and SE both differ; all required comparisons are examined and none match. Actual raw execution: No | No on observed failure, with both nonmatching comparison outcomes identified. This says nothing about total code absence |
| Failed attempted run | The complete required inventory is known; a stipulated raw-run log records failure before producing numbers, and both required outcomes have `not_run` with that reason. Actual raw execution: No | No on observed failed execution, with the log and affected outcomes cited. This has an attempted run, unlike the boundary-without-run case |
| Provision impossibility | Inspection stipulates a complete deposit starting only at final analysis data, absent required raw inputs and raw-to-analysis transformations, and a resolved boundary. No execution rows. Actual raw execution: No | No, explicitly provision-based impossibility. The absence claim depends on inspected applicable paths, not on an access failure. Run criteria remain unexamined |
| Incomplete comparison coverage | Inventory requires estimate and SE, but only estimate has a match row; SE remains unexamined. Actual raw execution: not yet assessed | Not yet assessed; neither Fully nor Partially follows from that all-match subset. Preserve the estimate's match and the missing comparison coverage |

The observed-partial rule also retains the existing case of some matches
plus a documented required `missing_input`: this is Partially once all
required comparison outcomes are accounted for. An unexamined outcome is
different from a known missing input. A blocker on the necessary inventory
or raw-source evidence leaves affected execution coverage unassessed rather
than converting a subset into numerical Partially. Raw boundary uncertainty
does not erase separately supported analysis-data comparisons.

The distinction between the failure and impossibility controls is deliberate:
identical No text alone hides different evidence. The revised instructions
require the basis in the row's evidence; they add no invented run or failure
criterion to an inspection-only assessment. All six report rows remain
visible, with Fully and not yet assessed included. Fixed three-column
templates leave unknown categories unmarked and state status/reason beside
the row. Only the separate list of individual statistic comparisons omits
matches. The same reading now appears in the reference, report step, and
plain-language rules.

## Frozen Blair dossier and preservation

The source remains replicator's read-only `t0002-investigation-20261126`
worktree, handoff `80c8a1df298e1dec8afca857875554fb0d5243da`. The new checks
verify exact handoff bytes for `scripts/compare_assess.py` and supplied
`controls.json`, and verify the frozen Blair assessment's hash and size
against the existing freeze manifest. No source or assessment was overwritten,
bytecode writes were disabled, and `reproduce.py`'s main function was never
invoked. Receipt-only appends to `REPORT.md` and `IDH-ticket-briefs.md` are
already recorded in the [1565 preservation evidence](../replicate-provision-1565/checks.json);
no new exact-match claim is made for those two documents. That artifact also
records the full frozen-artifact and provision-observation recheck, rather
than duplicating its bulk here.

The same frozen Blair assessment has an unresolved raw/analysis boundary,
empty execution coverage, unexamined `cra_*` and `crr_*`, and a paper blocker.
Its `out/reproduce.csv` is absent. The unchanged comparator still produces
raw execution Partially, matching the prior observation; the source's
boundary-without-run control still does too. These **actual old results**
remain in checks.json. Under the revised contract, the fixed dossier's raw
execution is **not yet assessed**: it supplies neither numerical comparisons
nor a verified resolved analysis-only impossibility. Retain the boundary,
inspected operations, and blockers. This is a contract-expected interpretation
of the preserved dossier, not a rewritten assessment, current comparator
conformance, or adjudication of Blair's historical deposit or I4R label.

No scientific scripts, new assessor cohort, paid provider calls, or external
messages to authors or I4R were used. Reference-target alignment, tolerated
adaptation, and matched output scope remain protocol decisions; no accuracy
or generalization estimate follows from these controls. Historical ticket
1562 receives a dated supersession note while its original observations and
then-current reading remain intact.

## Runtime identity and review limitation

The writer system description exposes GPT-6 and the OpenAI family, without
a served deployment ID or observed effort. Reviewer transport is the current
collaboration runtime, reusing task
`/root/raid_1565_1566/execute1565/consistency1565`. Its initial spawn requested
`gpt-6.1-sol` and medium effort with `fork_turns=none`; wave-two follow-up
reuses that context. The runtime returns a stable task path, but no served
model ID or observed effort. These identity fields remain runtime-masked;
the requested pin is route intent only. Reports use
`worker: model=runtime-masked · family=OpenAI`. This paragraph is the durable
masked-attribution evidence anchor. The seat provides same-family replication,
not independent review. The rejected external Anthropic attempt is not
retried or bypassed, and no machinery fix is included here.
