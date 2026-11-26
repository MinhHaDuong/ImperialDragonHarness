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
