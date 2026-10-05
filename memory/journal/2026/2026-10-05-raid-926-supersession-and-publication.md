# Raid 926/912/919: supersession and publication checkpoint

Context: the author selected tickets 0926, 0912 and 0919, lifted 0926's
deferral, requested verified superseded closure for 0912/0919, then explicitly
authorized publication of reviews and merges. The raid used independent
ticket worktrees and reviewed PRs [1204](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1204)
and [1205](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1205).

PR1205 closed and archived 0912/0919 with their abandoned v7 scopes stated;
the live v8 plan records their disposition. It passed 1497 tests with 2 skipped
and merged through `erg-pr-merge` as
`d0563d150b1b95d444bed4b942525319c98e9a61`. Its Correctness review
approved; Consistency and simplification each raised the same optional wording
consideration at `docs/2026-09-11-memory-implementation-plan.md:54`; the gate
recorded that the preceding paragraph already states the closed status and
approved without a source revision. Its public gate and subsequent integration
review are [recorded on the PR](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1205#issuecomment-6001318518).

PR1204 corrected the stale allocator premise in the collision script's comment
and recorded fresh binary controls in ticket 0926. Its initial review approved
`b1222b0ec0deaf60ef1c42e3c3695faa1b1242c1`. After PR1205 merged, its
own two source paths stayed byte-identical through a rebase and a clean
Regression review. PRs1206/1207 then advanced main while an intermediate
gate was running; that gate refused the stale base locally and was not
published. A second rebase preserved the two path contents; the current
reviewed head `d2f3dea49b1157961480cf4daa19c2197113d8b8` passed 1495
tests with 2 skipped, and its [current gate](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1204#issuecomment-6001552867)
approved. The two-test count difference reflects tests retired by PR1206.
At this checkpoint, PR1204 remains open while three required GitHub Actions
guard jobs wait in the hosted queue; seven other jobs have succeeded.

Review attribution capture remains pending for PR1205. The two implementation
agents inherited their launch model from the root session, whose exact
provider-qualified model ID was not exposed in the available trail. The
`writer:` field of the approved attribution contract names the PR producer;
substituting the wrap-up agent's model would misstate that fact. PR1204 will
also require this missing fact if it merges. No `kind: review-attribution`
record was written for either PR.

The available reviewer evidence is retained in the public PR reviews and
gate comments, with detailed local panel records at the time of this
checkpoint. Requested Codex agent reviewer launches were pinned to
`openai/gpt-6-sol` at medium effort. PR1205 used distinct Correctness,
Consistency, adherence, portable simplification and criterion-gate attempts;
its native Codex CLI review identified `openai/gpt-6.1-sol` at low effort.
PR1204's first panel had Correctness, Consistency and Doc-propagation attempts;
its second and third panels each had a fresh Regression attempt. Each round
also had adherence, portable simplification and criterion-gate attempts.
PR1204's native CLI review identified `openai/gpt-6.1-sol` at low effort in
round one and `openai/gpt-6-luna` at medium effort in rounds two and three.
All named attempts ran. The middle 1204 criterion gate produced a local
`ESCALATE` for the changed base, then the final gate approved the refreshed
base. No provider model version was exposed beyond these model IDs.

The live `origin/main` sweep found no second operational allocator comment
asserting a local-checkout-only scan. Search matches outside the corrected
script were historical imported project memory and the dated v8 integration
review. The memory v8 tracker 0909 had already been closed. No defect-fix
backfill was commissioned by either PR: 1204 changes a comment and ticket
evidence; 1205 records author-selected supersession.
