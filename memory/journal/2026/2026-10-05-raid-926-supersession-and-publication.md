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
The merge helper then closed/archived 0926 on the PR branch in
`9ab388807bfa7d9a82da02638011cac848e4420b`, a ticket rename and two
closure lines. At this checkpoint PR1204 remains open with protected GitHub
auto-merge enabled at 2026-10-05T19:39:16Z using `MERGE`, as the author
requested. All ten checks on the new closure head are queued. On the preceding
implementation head, seven checks succeeded and three guard jobs remained
queued. The PR's eventual merge is not yet confirmed.

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

## Final integration update, 2026-10-06

The earlier paragraphs record the 2026-10-05 checkpoint. GitHub completed all
ten required checks on PR1204's closure head and merged it at
2026-10-06T02:48:37Z as `ebd54f466644e82ef13c422340bb7a19a6ff8b1e`.
Ticket 0926 is archived with `Closed: autoclosed — PR #1204`. The final
integrated `main` contains both PR heads. On that tree plus this factual
wrap-up, `make check` passed 1494 tests with 2 skipped in 41.50 seconds.
The seven-day close-claim audit examined 30 merged PRs and 25 claims across
19 PRs, with zero dropped or unresolved claims. Tracker 0909 was already
closed; the 0912, 0919 and 0926 closure claims all took effect.

PR1213 independently captured a validated
[`review-attribution-pr1205`](2026-10-05-review-attribution-pr1205.md) record
using actual producer runtime proof. This supersedes the checkpoint's pending
capture statement for PR1205; the record is already on `main` and was not
rewritten here. PR1204 has no attribution record. Its producer's exact
provider-qualified model ID and effort are unavailable in this raid's
durable launch trail, so its required `writer:` line cannot be asserted.
The pending capture is reported rather than filled from another agent's
identity.

PR1204 review attempts retained for that pending capture: round one reviewed
`b1222b0ec0deaf60ef1c42e3c3695faa1b1242c1` with distinct Correctness,
Consistency and Doc-propagation agents, adherence, portable simplification,
native Codex CLI 0.160.0 `openai/gpt-6.1-sol`/low, and criterion gate. The
agent reviewer launches were pinned to `openai/gpt-6-sol`/medium. The first
gate approved. Round two reviewed
`b3ed9961a91fad10300b7a524208567a117d2189` with a fresh Regression
agent, adherence, simplification, native Codex CLI 0.160.0
`openai/gpt-6-luna`/medium, and criterion gate; its gate returned local
`ESCALATE` because main had moved. Round three reviewed
`d2f3dea49b1157961480cf4daa19c2197113d8b8` with fresh Regression,
adherence, simplification, native Codex CLI 0.160.0
`openai/gpt-6-luna`/medium, and criterion gate; all ran and the gate approved.
The round-three public gate is linked above. No anchored reviewer finding was
reported on PR1204; no model version beyond those IDs was exposed. The merge
helper's subsequent closure commit is a ticket rename plus two closure lines.

The final `origin/main` sweep found the corrected script header and no other
operational local-checkout-only allocator claim. Historical imported project
memory still contains old claims as dated evidence. No prior attribution
record anchors a changed line of the PR1204 comment, so no post-merge
defect-confirmed event was appended.

## Later main advance, 2026-10-06

After the final integration check above, PRs1209 and 1212 advanced main to
`bd2efaad7cbf0a44d57545a68ebf9394aaef8157`. The same wrap-up branch,
rebased onto that main, had no script, test or adapter diff. `make check`
then returned 3 failures, 1491 passes and 2 skips. A targeted run reproduced
the three failures in `tests/test_projection_validator.py`: launch still
refused with exit 1, but the stderr was the generic install direction while
the tests expected `double-fire` or `claude-code` details. The full test suite
on the earlier `6f976c33` main had passed as recorded above. Ticket 1039
records the post-1209 discrepancy without assigning an unproved intent to
the new message. The refreshed seven-day close-claim audit examined 30
merged PRs and 26 claims across 20 PRs, with zero findings. Wrap-up PR1216
remains open with its required pytest guard failing; auto-merge is not enabled
while that check is red.
