# Raid 9b9a7a — replicate feedback

The author requested all open harness tickets. The imported assessor tickets
were initially untracked in the primary checkout; PR2517 preserved them and
landed the raid's receiving review, plans, and feasibility notes before work
forked. Tracker1552 awaits integration of external replicator validation and
remains open. The cited CNRS project paths are absent on this host; supplied
counterexamples are acceptance scenarios, not independently rechecked papers.

## Observed events and author decision

PR2517's merge read-back succeeded, but the standard sync refused to overwrite
the author's untracked ticket files. Automatic approval review rejected a
proposed move out of the primary checkout. The raid copied and byte-verified
the originals at `/scratch/tmp/raid-9b9a7a-original-tickets`. The author explicitly
approved removal of the backed-up originals and the sync. A subsequent check
confirmed each original remained untracked and byte-identical before removal;
standard sync then fast-forwarded main. The backup was retained.

Ticket1560 was already met: the link existed, and a fresh Claude session
successfully invoked the Skill tool. Its closure is PR2518. The installer
already discovers current skill directories when `idh install` runs; no
installer change was made.

Ticket1559 already had a pushed implementation in another session's locked
worktree. A fresh raid worktree reused its commit while preserving original
authorship; the old worktree was left untouched. Zenodo API metadata independently
confirmed the shipped files' bytes, hashes, versions, attribution, and licence.
PR2519 landed after REVIEWED gaze, round-1 APPROVED gate, and a byte-identical
implementation diff comparison across its rebase. The no-fit review concern
and its disposition remain on notes. Per-ticket evidence is under
`design/1559-template-verification/`.

The initial main baseline is recorded in `memory/evidence/raid-9b9a7a/baseline.txt`.
Runtime identity limitations are recorded in
`memory/evidence/attribution/2026-11-26-raid-9b9a7a-runtime.md`.

PR2521 closed ticket1561: all four completeness criteria cover the whole
paper, with output inventories and a revised example/mapping. Main-result
ACRe success remains distinct from whole-paper table coverage. Supplied
Arechar/Moscona cases and synthetic positive controls are documented in
`design/replicate/1561-package-coverage-walkthrough.md`; no external numerical
validation was claimed. Gaze was REVIEWED, integration CLEAN, and the first
gate APPROVED.

PR2522 closed ticket1562: raw inputs are documented starting extracts,
cleaning includes transformations embedded in analysis scripts, and provision
is component-specific. A missing input or failed execution does not itself
prove incomplete code. The scenario walkthrough is under
`design/replicate-assess/1562-boundary-walkthrough.md`. Final gaze was
REVIEWED, integration CLEAN, and the first gate APPROVED.

The review trail retains an aborted setup: it emitted the prior forge head
and request while its anchor and checked-out tree named the newer pushed
head. No seat launched for that setup. The cause was not isolated. A fresh
setup and completed review bound the final head before gating; no gate round
was spent on the inconsistent setup. Raw attempt identities remain in notes;
factual captures mask model identifiers the runtime did not expose.

PR2523 closed ticket1563: blocked evidence remains unexamined, blind supplied-URL
assessment excludes helper searches/prior notes, archive hashes identify exact
representations separately from local observed SHA-256, and generated analysis
inputs require an inspected complete producer chain. Resumption revisits stale
access and criteria. JSON examples parsed; the actual old/new level snippets
were exercised with a synthetic grid, with results in
`memory/evidence/raid-9b9a7a/level-example-check.txt`. This did not validate the
external CIRED grid or named empirical packages.

Epoch 1's semantic REVIEWED answer existed, but attribution capture failed on
an absolute evidence anchor and emitted a placeholder identity. Epoch 2 reread
the same head and completed masked capture. Both attempts remain in raw notes;
the factual capture conservatively masks the historical placeholder and retains
all reported seats. Gaze end epochs were not recorded for these attempts;
the timing evidence names the missing measurements rather than deriving them
from run IDs. Final gate was APPROVED in round1; wave integration was CLEAN.

## Completion

The initial actionable queue1559-1563 is closed. PR2517 imported tickets and
plans; PR2518 verified the already-met loader issue; PR2519/2521/2522/2523
landed the skill changes. Exact merged heads were confirmed on remote main.
Tracker1552 remains open for the external replicator validations and integration
review. The external receiver path is absent, so no completion log was written
into a substitute project. Incoming PR2520 (ticket1564) and PR2516 belonged to
other work and were left unchanged.

Timing rows/table and recognized-bump counts are under
`memory/evidence/raid-9b9a7a/`. Tooling/deliverable ratio is inapplicable to this
harness product. Blind assessment was checked by scenario review. Held-out empirical
benchmark validation remains the external tracker work. No rules or STATE
changes were made.

The standard full after-merge run passed on main after PR2523; its recorded
summary is `memory/evidence/raid-9b9a7a/main-after-merge.txt`. The bounded
replicate-contract union sweep found no retired conflicting instructions;
positive control and search scope are in `union-sweep.txt`. No qualifying
follow-up ticket was created. Historical walkthrough breadcrumbs were retained;
no live Markdown reference was broken by ticket archival.
