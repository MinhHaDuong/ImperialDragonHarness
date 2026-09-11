# Memory implementation plan

**Publication date:** 11 September 2026  
**Préparé par ChatGPT prompté par Ha-Duong Minh**; realigned to v7 by Claude on
the same prompting  
**Phase:** Plan — no runtime implementation in this change  
**Design baseline:** [v7](./2026-09-10-dragon-memory-design.md). v6 was adopted in
[PR #903](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/903) at
`a68fd1ed` and is [frozen](./2026-09-10-dragon-memory-design-v6.md); v7 closes
the four conditions of the
[acceptance review](./2026-09-10-dragon-memory-design-review-fable-acceptance.md)
and settles the [nomenclature](./2026-09-10-dragon-memory-design-nomenclature.md).
The architecture is unchanged, so no ticket's scope moves; four acceptance
obligations gain an owner, and the names the train writes are now fixed.

## Executive summary

Retain ticket identities and append their scope-change history. The v4 train
cannot be dispatched unchanged: it promises mandatory residency, destructive
promotion and compulsory subjective annotations that v6 rejects. This plan
reuses its useful seams and adds six bounded delivery workpackages, 0920–0925.

The first usable milestone is one project, one small shared snapshot and one
runtime adapter operating from a disposable offline clone. It does not wait for
all adapters, corpus-wide migration, model annotations, embeddings or a broad
predicate grammar.

One internal Python library owns memory mechanics. A thin CLI and thin runtime
adapters reuse it. Editorial dreaming and compilation are distinct responsibilities;
pending synthesis proposals do not block publishing accepted bodies. Concurrency
uses Git isolation and optimistic revision checks.

## Contents

1. [Ticket map](#ticket-map)
2. [Execution order and milestones](#execution-order-and-milestones)
3. [Scope changes from the previous train](#scope-changes-from-the-previous-train)
4. [Design coverage and acceptance gates](#design-coverage-and-acceptance-gates)
5. [Validation and adoption](#validation-and-adoption)

## Ticket map

Existing ticket filenames remain stable despite revised titles, preserving links.
The following table is the scheduling contract; `Blocked-by` headers mirror it.

| ID | Deliverable | Depends on | Place in programme |
|---|---|---|---|
| 0911 | Minimal schema, internal library and thin CLI boundary | — | Foundation |
| 0917 | Baseline and qualified historical provenance | — | Foundation |
| 0908 | Legacy inactive-marker import | 0911 | Pilot prerequisite |
| 0915 | Canonical-owner routing and validated admission | 0911 | Pilot prerequisite |
| 0920 | One portable project and bounded shared snapshot | 0917, 0908, 0915 | Pilot |
| 0910 | Deterministic compiler and coherent publication | 0920 | Pilot |
| 0921 | Loader, recent revisions and optimistic integration | 0910 | Pilot |
| 0922 | Lexical task recall and knowledge-hint integration | 0921 | Pilot |
| 0923 | First runtime adapter and offline live smoke | 0922 | First usable milestone |
| 0924 | Remaining Codex/Pi/Claude Code adapters | 0923 | Broader delivery |
| 0918 | Channel-attributed behavioural evaluation and calibration | 0923 | Parallel measurement |
| 0912 | Automated candidate discovery without prescribed outcomes | 0923; deferred | Optional, not closure gate |
| 0913 | Staged rollout and retirement of replaced machinery | 0924, 0918 | Broader delivery |
| 0916 | Manual editorial review/apply contract, sources retained | 0923 | Editorial support |
| 0925 | Harvesting through existing governance | 0923 | Editorial support |
| 0909 | Union/integration review and programme closure | 0913, 0918, 0925, 0916 | Tracker, final gate |
| 0914 | Additional predicates for demonstrated failures | 0923; deferred | Optional, not closure gate |
| 0919 | Sample-based quality annotation experiment | 0918; deferred | Optional, not closure gate |

The tracker is blocked until its final integration work is meaningful; it must
not appear as an independent coding task. The optional tickets retain the
repository's `deferred` label, which suppresses dispatch even after their
prerequisites land. They require new evidence and explicit reactivation, not
automatic scheduling because the baseline is complete.

## Execution order and milestones

**Foundation.** Start 0911 and 0917 independently. Schema and the core library
must precede semantic migration. Preserve a baseline before bulk edits, but
do not claim that a later commit destroys retained Git history. Distinguish
first observable Git appearance from real creation and mechanical touch from
semantic freshness.

**First usable milestone.** Complete 0908/0915, then 0920 → 0910 → 0921 →
0922 → 0923. Use fixture corpora while building, and one representative project
for live evidence. The pilot keeps particular observations, readable inactive
records and a committed shared snapshot. Admission, publication and recall must
work without model services.

The first runtime is chosen and justified in 0923 from accessible representative
execution evidence. Remaining runtimes use the same contract; the choice does
not grant permanent privilege or permit runtime policy forks.

**Expansion.** After 0923, remaining adapters, initial behavioural evaluation
and manual editorial review/harvesting may proceed independently. Broad migration
and cleanup follow verified adapter coverage and 0918 evaluation against
predeclared margins. Unmet margins need remediation or an explicit scope/risk
decision before broad activation or retirement; do not delete the old path before
its replacement works for its consumers. Migration of another repository uses
that repository's normal branch/review process.

**Editorial work.** Candidate groups are opportunities, not instructions to
merge. A generalisation gets a new UUID and source relations; unchanged scope
expansion preserves identity; supersession is a separate withdrawal. Shared
changes follow existing review. Harvested procedures go through normal adoption,
with evidence preserved and old prescriptions explicitly qualified. Harvesting
can start directly from particular lessons after 0923, without waiting for
candidate grouping or generalisation. The core editorial workflow supports
manual judgments; automated/model-assisted generalisation remains optional.

**Closure.** Tracker 0909 reviews the union of the three branches of work:
delivery/rollout, evaluation, and editorial/harvesting. All core descendants
must be completed or explicitly re-scoped through a recorded decision before
closure. Rerun relevant evaluation on the integrated result, including later
generalisation and harvesting scenarios; pilot measurements cannot certify
features that did not yet exist. Optional predicates and subjective backfill do
not block it.

## Scope changes from the previous train

- **0908** becomes compatibility import. No generalisation retires a particular
  merely because a similar shared body exists.
- **0911** owns schema and package foundation. The migration moves to 0920/0913,
  and generated views belong to 0910. Correct the contradictory flat-`type`
  test. No compulsory pair of schema libraries without a dependency assessment.
- **0910** compiles a combined available pool and records inputs. It drops
  mandatory residency, tier quotas and dependency on broad predicate machinery.
- **0913** moves behind working consumers. Cleanup is not a prerequisite that
  removes the old discovery path before the new one exists.
- **0914** becomes optional predicate extension. Lifecycle and UUID references
  are baseline work, and unknown applicability is never relabelled true.
- **0915** owns actual admission mechanics, not a survey that can declare
  scoring-only enforcement sufficient. Routing correctness remains judgment.
- **0912/0916** separate optional automated discovery from core manual review/apply.
  Defer 0912; 0916 accepts manually supplied proposals and does not depend on it.
  Remove predetermined promotion direction, automatic tombstoning, an eternal
  rejected-pair ledger and a run lock as the concurrency model.
- **0917** preserves useful provenance without false expiry urgency.
- **0918** measures actual delivered context and task outcomes. Successful
  below-cut recall is not automatically a ranking failure.
- **0919** is an evidence-driven optional sample experiment. Missing subjective
  annotations never make every existing body unrankable.

## Design coverage and acceptance gates

These are acceptance responsibilities within the existing train, not additional
subsystems. Each owner supplies failing controls and reviewable evidence.

**The four v7 gates.** v7 rewrote §12.1 so that every row names a mechanism whose
removal makes it fail. Four rows are new or newly deterministic, and each needs
an owner in this train rather than a new workpackage:

| V7 §12.1 gate | Owner | Note |
|---|---|---|
| Predicate with an operator outside the closed subset, a path outside its declared root, or a payload with a side effect if interpreted → rejected at entry, *unknown* at evaluation, sentinel verifiably absent | 0915, with the grammar **and evaluator** from 0911 | The sentinel is the positive control separating "did not execute" from "did not look". It must exist before the first `shared-snapshot/` is committed in 0920, because a replica carries predicates authored in another project |
| Same UUID, accepted revision in C differs from the revision ranked in G → G's text never rendered | 0921 | This is the invariant the whole G/C construction exists for; three neighbouring rows each miss it |
| Adapter's declared native memory root disjoint from the canonical root; foreign line in the generated view discarded and reported, no model in the loop | 0923, parity 0924 | Recorded **known red** in v7. **0920 clears it**, not 0913: IDH's repository *is* `~/.claude`, so the store cannot leave it, and what moves is its position relative to the runtime's *declared* native root — `memory/` → `memory-shared/` and `projects/-home-haduong--claude/memory/` → `memory/`, with every hard-coded reader repointed |
| Compiler never creates, modifies or moves a canonical body; processed manifest excludes uncommitted bodies and unmerged branches | 0910 |
| §8 growth monitoring — body-count growth, consolidation duration and unresolved backlog, exposed as `hoard weigh` | 0910 | Replaces two absence-shaped rows that no removable mechanism could fail |

**Names are settled.** v7 §17 fixes what this train writes, so 0911 adopts rather
than chooses: the internal package and its CLI are `hoard`; a project's memory
root is `memory/` in its own repository and the shared store is `memory-shared/`
at harness level, with `shared-snapshot/` unchanged under `memory/`. The verbs
are `assay` (§5 admission and routing), `reckon` (§6.1/§7.3 catalogue and ranked
manifest), `seal` (§10.1 snapshot and handover), `sift` (§6.3 task recall),
`shed --by` (§4.3 supersession), `disown` (§4.3 retraction) and `weigh` (§8
growth monitoring). `shed` without `--by` must not parse and `disown` must take
no successor: §4.3's malformed call is unwritable, not rejected afterwards.

| V6 contract | Owner | Evidence required |
|---|---|---|
| UUID/lifecycle, project identity and minimal bounded applicability grammar | 0911; admission 0915 | Conflicts, invalid operators and true/false/unknown fixtures |
| Portable snapshot and recurring refresh | 0920; publication 0910; loading 0921 | Verified ancestry, divergent replicas, dependency gaps, withdrawals and coherent snapshot/view handover |
| Reproducible coherent publication | 0910 | Explicit dreaming acknowledgement; compiler-only republishing cannot clear Recent; rendered cost and interrupted handover |
| Admission and later lifecycle edits | 0915; history 0922 | Audience/scope judgment, atomic status/move/link repair, redirects excluded from ordinary recall |
| Current withdrawals, recent freshness and backlog | 0921 | Withdrawal before selection; aged entries remain provisional/searchable |
| Damaged or absent publication | 0921; recall 0922 | Validated local browse/search survives; broken enumeration cannot pass as empty success |
| Proactive recall and material task changes | 0923; parity 0924 | Actual pre-action delivery, refresh, compaction recovery and cumulative cost |
| Behavioural readiness before broad rollout | 0918 → 0913 | Predeclared margins, repeated matched tasks and an explicit rollout verdict |
| Editorial changes and harvesting on the completed system | 0916/0925; final 0909 | Preserved local exceptions and current procedure followed after later amendment |

Core editorial workflows are part of programme closure, while automated model
integration, individual proposals and changes remain optional. Manual reviewed
judgments and no-change passes suffice for the base. Harvesting is independent
of generalisation. Automated candidate discovery (0912), extra predicates (0914)
and quality annotations (0919) are deferred, outside closure requirements.

## Validation and adoption

Each implementation ticket carries context, relevant files, actions, focused
fixtures, verification, invariants and exit criteria. Tests must expose a real
failure: empty enumeration, unobserved delivery or a missing measurement cannot
pass as success. Classifying decisions, judging equivalence and agent adherence
remain behavioural evaluations, not deterministic promises.

The first smoke must demonstrate all three delivery components in one offline
pilot, rather than merely checking skill wording. Additional runtime smokes
verify native-memory isolation, context boundaries and declared limitations.
Record model/runtime versions, denominators, uncertainty and cost for behavioural
comparisons. Set numeric acceptance margins before trials; do not invent them
from a single passing run.

Token figures 1,500 / 500 / 2,000 remain proposed calibration inputs, not newly
ratified defaults. No third-party component is licence-cleared by this plan.
0911 owns the small build/reuse assessment of the MemU patterns identified in
the companion comparison before implementing equivalents. Record the actual
revision, licence and obligations before copying, adapting or
depending on a component. Reuse existing knowledge-hint mechanisms and canonical
decision records; introduce no new memory governance database.

This planning PR changes handoff tickets and this plan only. It does not close
implementation tickets, change runtime behaviour or revise the adopted
architecture. Preserve existing ticket logs; Git retains the former scope.

Before merging the planning PR, recheck allocated IDs 0920–0925 against current
main and open-PR changed files. The initial scan found no open PRs and used
merged PR #900 as a positive control for ticket-file enumeration. Allocation
remains optimistic; on a real collision, follow `tickets/AGENTS.md` recovery.
