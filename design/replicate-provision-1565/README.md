# Provision coverage contract: ticket 1565

Date: 2026-11-26. This is a documentation repair and a contract walkthrough,
not a new replication experiment. The receiving Imagine, scope, and serial
wave plan are recorded in the ticket history carried by this branch.

## Interpretation and scope

Partially means demonstrated provision with a verified missing required
item or stage for that component. Inspected lower bounds with unresolved
coverage remain not yet assessed. Fully requires complete whole-paper
coverage, including applicable supplements. A verified gap remains Partial
when another part of that component is blocked; the blocker cannot establish
or erase the gap. Contradictory evidence requires reconciliation.

This applies to raw inputs, cleaning operations, analysis inputs, and
analysis code. It removes the scripts-only shortcut and the ambiguity-only
provision shortcuts. It preserves the scope of the package assessment,
preselected main-result ACRe run criteria, matching tolerance, and execution
objectives. Ticket 1566 owns the remaining raw-execution exception. This
branch neither repairs the downstream comparator nor claims it implements
this interpretation. Matched validation targets, equivalent-format adaptation,
and output scope still require the protocol choices identified in the source
report. No new cohort or accuracy claim is authorized by these checks.

## Independently constructed contract controls

These are hypothetical evidence dossiers constructed for the revised
instructions, distinct from the source controls. Read each case through the
four steps: establish applicable outputs/paths; retain positive facts;
check for a demonstrated gap; apply the category. They are manual scenario
checks of a contract, not outputs of a second evaluator or tests of wording.
The review seat checks these expected readings against the revised reference.

For each component below, define an applicable primary output P and appendix
output A, with a third path B used only in the blocker variation. Their
required inputs and operations are specified in the inventory. A verified
absence means inspection of the relevant deposited files and producer paths
has established the stated item is missing; a staged subset or failed
retrieval would not suffice.

| Component | Positive fact for P, retained in every scenario | Verified gap for A in the gap scenario | Full scenario evidence |
|---|---|---|---|
| Raw data | Required starting extract `p.csv` is inspected under the documented raw boundary | Required raw extract `a.csv` is verified absent from the deposit; no supplied substitute or producer supplies it | Every required raw extract for P and A is inspected under the documented boundary |
| Cleaning code | Inspected `clean_p` performs the documented raw-to-analysis transformations | A required panel-build stage for A is verified absent, although some A recodes are present | Inspected operations cover every transformation for P and A, including operations embedded in analysis scripts |
| Analysis data | Required analysis input `p.dta` is inspected | A required analysis input is verified absent and inspection establishes no complete supplied producer chain | Every required analysis input is deposited or has an inspected complete producer chain with all required inputs, dependencies, and expected paths |
| Analysis code | Inspected estimator code produces P's specified statistics | Required plotting code for A is verified absent after inspecting applicable code paths | All required estimation and plotting code for P and A is mapped and inspected |

Apply these variations independently to **each** component in that table:

| Control | Evidence state | Contract-expected provision category and evidence treatment |
|---|---|---|
| Unknown inventory | P's fact is known; original-paper/supplement inventory is unavailable, so A's applicability and coverage cannot be examined | Not yet assessed. Keep P's fact and unresolved coverage visible; completeness stays `a_evaluer`. Accessible scripts alone do not create a gap |
| Blocked inventory | Same positive fact; a documented access blocker prevents inspecting A's contents or inventory | Not yet assessed. Record affected criteria in `a_evaluer` and `blocked`, with attempted source and next step; blocked access proves no absence |
| Verified gap | P is provided; A is applicable and has the component-specific verified gap described above | Partially. Evidence identifies the present item, required missing item/stage, applicable output/path, and inspection basis; record the corresponding partial criterion |
| Complete inventory | Complete applicable inventory and the component-specific full evidence described above | Fully. Establish the corresponding completeness criterion; P's fact alone would not suffice |

For the verified-gap control, additionally block inspection of B. Every
component remains Partially: P demonstrates provision and A's verified gap
already disproves completeness. Preserve B's blocker too. In the cleaning
case, an unavailable input dictionary with otherwise complete cleaning code
belongs to raw/input availability, rather than proving a cleaning-code gap.

Two further ambiguity controls exercise the old shortcuts. An assembled
panel with an unresolved raw/analysis boundary leaves raw provision not yet
assessed while preserving the panel's inspected facts and boundary evidence.
A script with identified recodes but unexamined panel assembly leaves cleaning
provision not yet assessed. A separately verified missing required assembly
stage changes that cleaning control to Partially, even with a blocked
supplement. A filename difference without a missing program changes no gap
finding. These readings distinguish inspection uncertainty from incomplete
provision without executing any package.

## Read-only recheck of the unchanged source

[checks.json](checks.json) is generated evidence from a read-only Python
invocation. It records actual hashes and byte counts, supplied controls,
and the unchanged comparator's provision results for the frozen dossiers.
Its method imports `scripts/compare_assess.py` with bytecode disabled, calls
`derive_table` in memory, and asserts equality with the saved control and
frozen observations. It reads the freeze manifest and asserts every listed
artifact's SHA-256 and byte count. It never invokes `reproduce.py`'s main
function and writes only the local checks artifact in this harness tree.

The source is replicator's `t0002-investigation-20261126` worktree, with
handoff commit `80c8a1df298e1dec8afca857875554fb0d5243da`. The generated
artifact records five source comparisons: three exact files; `REPORT.md`
and `IDH-ticket-briefs.md` have only the appended receiver receipt beyond the
exact handoff-byte prefix. An initial exact-match check stopped at that
append; the subsequent check verified the precise append-only difference.
All 50 frozen deliverable hashes and sizes match; all 40 frozen provision
observations reproduce. These numbers come from the artifact, not a new
scientific run or a deposit inventory certification.

| Supplied source control | Actual unchanged comparator result | Revised contract-expected reading |
|---|---|---|
| `scripts_only_unknown_inventory` | Analysis code Partially | Not yet assessed; inspected models remain positive facts |
| `scripts_only_blocked_inventory` | Analysis code Partially | Not yet assessed; the supplement blocker remains explicit |
| `positive_complete_code` | Analysis code Fully | Fully, conditional on the stipulated verified complete inventory |
| `raw_boundary_without_run` | Raw provision Partially; raw execution Partially | Raw provision not yet assessed. The execution defect is separately owned by 1566; no numerical execution conclusion is drawn here |

The supplied controls contain complete criterion partitions; they are
unchanged. The independently constructed verified-gap cases are in the
walkthrough, rather than pretending the supplied controls include that case.

For the same frozen Blair dossier, `checks.json` preserves the actual
Partially result and source evidence for each provision row. On that fixed
evidence, the contract-expected interpretation is not yet assessed for all
four provision rows: raw evidence describes an unresolved boundary; cleaning
evidence describes an unresolved panel assembly source; analysis-data and
analysis-code evidence explicitly cite unavailable whole-paper coverage.
The observed files, recodes, estimator calls, and program-definition check
remain useful lower bounds. None of those cited reasons verifies a missing
required item across the applicable deposited paths. This is an interpretation
of the preserved dossier, not a revised assessment file or a claim about
Blair's historical package. Other frozen rows are rechecked for preservation;
no blanket recoding or post-unseal reference rationale is injected.

## Runtime identity and review limitations

The writer system prompt exposes `GPT-6` and the OpenAI family, without a
served deployment ID or observed effort. Requested pins are recorded
separately from observed identity. The reviewer route is one same-family
OpenAI consistency seat requested as `gpt-6.1-sol` at `medium`, through the
current collaboration runtime. That route is proportionate to the narrow
contract consistency risk, and adds replication rather than cross-family
independence. The previously rejected external Anthropic attempt is not
retried or bypassed. No external independent review is claimed.

Runtime launch evidence: the collaboration `spawn_agent` call returned
`/root/raid_1565_1566/execute1565/consistency1565`. It requested
`gpt-6.1-sol` and `reasoning_effort=medium` with `fork_turns=none`.
The tool returned that stable task path, without a served model or observed
effort field. Model identity and effort are therefore runtime-masked, not
measured from the requested pin. The report header uses
`worker: model=runtime-masked · family=OpenAI`; this paragraph is the stable
repository evidence anchor for masked attribution. Review completion is
verified from the landed report and recorded in review notes, separately
from this launch record.
