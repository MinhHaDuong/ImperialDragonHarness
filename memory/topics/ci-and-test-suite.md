# CI and the test suite

Scope: measurements and author decisions about the forge CI, the local CI
runner and the test suite's cost, 2026-10-02 to 2026-10-13. Standing
procedure lives in `skills/merge/SKILL.md` (where the local CI runs) and in
ticket 1045 (local merge gate, closed 2026-10-21 by PR 1625; see
[merge flow](merge-flow-and-review-evidence.md)); this topic records evidence
only. Forge Actions were later disabled repo-wide, and `pytest -n` now comes
from `scripts/pytest_workers.py` (ticket 1215), not a fixed `-n 4`.

## Supported observations

Suite economics (2026-10-02, PRs #1111, #1118, #1120, #1122): full `make
check` went from 81 s to 33 s and check-fast from 18.4 s to 2.9 s, through
re-tiering spawn tests, `pytest-xdist -n 4` after a worker-safety audit, and a
relay-wait knob. Lint sits at about 2 s, the pytest import floor. The author
re-scoped the hermeticity guard (0940) to the post-0945 threat model and
accepted its adversarial tail as disclosed.

Runner nondeterminism (2026-10-02, PR #1133): a guard verdict flipped across
GitHub runner allocations on blob-identical trees because one tool built a
control-byte stream and a second tool re-parsed it. Removing the second tool
fixed it; the same class was then closed on the whole ref (1015). CI now
prints awk, grep and bash versions.

Local CI (2026-10-05/06, while hosted runners were not provisioned): `make
check` is not equivalent to CI.yml's ten jobs. `act` 0.2.89 under rootless
podman with a custom image matched the forge on commit `715c59d7` (same ten
jobs, 1487 passed, 10 skipped). Measured traps: `act -j` honours only the last
`-j`; act's default checkout drops `.git`; a podman socket path over the
~108-byte unix limit made a negative-control series report nine catches while
no job had run. The ruleset requires seven of the ten checks with no bypass
actor; a bypass actor was added then removed at the author's request ("I would
rather wait than bypass"). A hand-started `podman system service --time=0`
outlived the session's `/roar` by 12 h 42 min and was found only because the
author asked; the author settled that this is experiential memory, not a
change of instructions.

Forge waits. A required `pytest-guard` stayed `in_progress` 1 h 49 min on
PR #1245 (usual about 1.5 min), cause not established; a blocking
`gh pr checks --watch` was stopped at the author's request. A Claude Code
native note records the author's preference that followed (preserved in the
[2026-10-07 dream](../hoards/2026-10-07-second-dream.md)); it agrees with the
event and adds no rule here. Forge-check waits twice returned on a stale
rollup before the new head's checks existed (2026-10-06).

Refresh, 2026-10-08 to 2026-10-13. Single CI failures that passed on rerun,
with causes not established: `test_attribution_query` (a temporary-repo
`git merge` exited 128, PR #1263) and `test_check_cross_pr_ticket_collision.sh`
(PR #1270). An Opus review found 0 failures in 48 parallel runs of the
collision suite. It also found that shell suites skipping every check reported
PASSED, fixed by mapping exit 77 to a pytest skip. The collision script, run
from a worktree whose branch already has an open PR, reports that PR's own
ticket, because `SELF_PR_NUMBER` comes only from the CI workflow. On padme,
uv environments changed the last float digit of tournament outputs, while
system Python (matplotlib 3.10.8, the committed provenance) reproduced main
byte for byte. A CI test needing `pdftotext` now skips where the binary is
absent. Full `make check` counts rose from 1514 passed (2026-10-08, local, wave A1)
to 1606 (2026-10-13, the tested union commit of 1091 and 1092). Per-host differences came from missing tools on doudou and a
network test on a secretless box.

Local CI. Ticket 1088 (PR #1368, 2026-10-12): the shared runner exits 3 with
an explicit SKIP in a repository without a committed workflow. During that
wrap-up the author asked, "What did we spend the last 2 hours on?", asked for a
committed record for a later inefficiency postmortem ("I want SCIENCE"), and
deferred the analysis. The duration was not measured separately. On
2026-10-10, `local-ci.sh` ran twice, once on a ticket-only change, and the
author asked why a 52-line ticket took over 13 minutes; no per-step timings
existed.

Forge waits, continued. `erg-pr-merge` refused while checks ran, and a caller
that ended its turn left PR #1345 open for about an hour, although all checks
had passed within two minutes (2026-10-10). Ticket 1082 (PR #1352) made the
helper arm auto-merge on pending checks and added the one-shot `erg-pr-status`
(exit 0 merged, 1 failed, 2 pending). The author had asked that it not be a
sleep loop. On 2026-10-13 a merge attempt failed because required checks had
not yet registered, and auto-merge was armed after they appeared.

## Author decisions recorded in the sources

No `pre-push` hook calling the local runner. Ticket 1045: a local merge gate
replaces the forge's required checks after a review of the CI's content.
"Run the local CI on padme when it is reachable" was placed in
`skills/merge/SKILL.md` after the resident-rules budget test refused it in
`rules/git.md`.

## Later measurements (2026-10-14 to 2026-10-15)

The [read-back census](../journal/2026/2026-10-14-readback-rule-and-1090-merges.md)
reported 379 separate read-back turns out of 15,496 main-thread turns (2.4%).
Its three mutation categories total 1,001 despite a stated population of 1,036;
the 35-mutation difference is unresolved. Of 26 inspected reissued mutations,
none showed a silent failure; the original 2026-09-04 motivating failure was
not re-probed. PR #1404 changed the rule to same-command read-back; this
limited observation does not invalidate that rule.

The [1090 remeasure](../journal/2026/2026-10-14-roar-remeasure-1090.md)
withdraws the apparent 16 → 14 turn improvement: comparable October solo
Claude Code medians were 10 before (53 roars), 12.5 after (14). Smaller start
contexts predated 1084; causation was not isolated. The colocated saved
`analysis-output.txt` uses broader before/after populations (104/13 solo)
and is not an exact numeric reproduction of that October table. Later 1098
savings remain unmeasured; see [cleanup](branch-cleanup-incidents.md).

[Raids 1080/1089](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md)
finished exact integrated-main checks at `fea2413a`: 1595 passed, 3 skipped,
47.78 s. The [rename integration](../journal/2026/2026-10-15-raid-1101-1103-1104-integration-pending-attribution.md)
records 1627 passed, 3 skipped, 50.26 s on `ec5571a7`; local container CI
recorded 1620 passed, 10 skipped. These are different execution environments,
not failed count reconciliation. Earlier pending CI statements in raw reports
remain historical, with completed results recorded separately.

## Later measurements (2026-10-15 to 2026-10-29)

Counts. `make check` on integrated trees: 1640 passed (2026-10-15), 1733 to
1763 (2026-10-19), 1908 (2026-10-20), 2053 to 2238 (2026-10-21), 2179
(2026-10-26), 2430 to 2551 (2026-10-27), 2829 and 3009 (2026-10-28), 3041
collected (2026-10-29), each with 3 or 4 skipped. Container pytest skips rose
from 10 to 95 on 2026-10-19, unexplained in the entries. Sandboxed runs failed
on socket denial and passed unsandboxed (#1415, docs refresh).

Gate wall time. PR #1583 made the `worktree-gc.sh` liveness scan a single
`readlink` over `/proc`: 14 GC tests had taken about 21 s each on a host with
10,942 processes, and `make check` fell from 353 s to 76 s
([1583](../journal/2026/2026-10-21-gc-liveness-scan-lazy-pr1583.md)). A trace
analysis of 334 runs (median 78 s, p90 201 s) found the smart-testing tests held
38% of serial time; the author retired the helper and moved to 8 workers
([gate wall time](../journal/2026/2026-10-21-pulse-gate-wall-time.md),
[pulse](../journal/2026/2026-10-21-pulse-testing-expert-1541.md)). On
2026-10-29 a quiet-host `make check` took 35.0 s against a field median of about
75 s; the entry's hypothesis (about 80%) is CPU sharing with parallel sessions
and arena coders. Ten ABBA pairs of `-n 24` and `-n 32` differed by a mean
-1.6 s (sd 9.1 s), so the cap stays 24 and the worker rule stays adaptive
([contention](../journal/2026/2026-10-29-test-doctor-gate-contention.md)).

Flakes, cause not established: `test_pool_runs_every_item_and_counts_failures`
(forge and local, 1 of 36 in one stress run, 0 in 2550 replica trials), a
sibling pool test, `test_kill_groups_reaches_the_whole_group`, a Zotero field
test, a collision-shell assertion on #1415, and after-merge reds 1295 and 1322.
Isolated causes: a Zotero 401 traced to an xdist port collision (1258, 1259); a
`.git/config.lock` race in `review_notes.setup()`, 7/60 failures before and 0/60
after (PR 1873); a byte-snapshot test tripping on git maintenance removing
`maintenance.lock`, fixed by disabling auto maintenance in the fixture
([fourth hoard merge](../journal/2026/2026-10-15-fourth-hoard-merge-and-maintenance-fixture.md)).

Environment traps. Hunt's `TMPDIR=$W/.tmp` advice made census, coherence and
harness-doctor tests fail in coder worktrees (seen 2026-10-21, 10-26, 10-27). A
test needing poppler passed locally and failed on CI (#1447). Install tests
leaked into the real `~/.local/bin` and inherited PATH (#1759, #1767). Direct
`pytest tests/test_attribution_record.py` errors on import while `make check`
passes ([1302-1306](../journal/2026/2026-10-28-raid-1302-1306-wrapup.md)).
Resident budgets refused growth several times: skills 6209/6200 passed a
pre-rebase lint, the rules set sat at 17,795 of 17,800, and two PRs that each
passed alone composed to 18,317 against 18,200 after the first merged; the
budget became 18,350 ([composition](../journal/2026/2026-10-29-raid-6958fe-resident-budget-composition.md)).
The author ruled "REMOVE WORDING PINS" on PR 1778; thinning followed in PR #1782.

## Sources

- [Suite economics](../journal/2026/2026-10-02-session-suite-economics.md)
- [Hunt 0875 runner nondeterminism](../journal/2026/2026-10-02-hunt-0875-runner-nondeterministic-guard.md)
- [Raid 1015](../journal/2026/2026-10-02-raid-1015-annotation-collision.md)
- [Local CI and act equivalence](../journal/2026/2026-10-06-local-ci-act-equivalence.md)
- [Leftover podman service](../journal/2026/2026-10-06-leftover-podman-service.md)
- [0913 close path, stale-base CI](../journal/2026/2026-10-06-0913-dispatch-close-path.md)
- [PR #1245 stuck check](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md)
- [Routing A1 and A0 to C, flakes](../journal/2026/2026-10-08-llm-routing-plan-and-wave-a1.md), [waves](../journal/2026/2026-10-08-llm-routing-waves-a0-to-c.md)
- [Review round, suite findings](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md) and [round two](../journal/2026/2026-10-09-routing-review-round-two.md)
- [Padme float drift](../journal/2026/2026-10-09-tournament-report-padme-env-float-drift.md)
- [Merge script CI refusal](../journal/2026/2026-10-10-merge-script-ci-refusal-and-ticket-1082.md) and [raid 1082](../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md)
- [Permissions, local CI runs](../journal/2026/2026-10-10-permissions-allow-all-and-idh-install-sync.md)
- [Local CI wrap-up](../journal/2026/2026-10-12-local-ci-wrap-up-inefficiency.md)
- [Raid 1084/1085/1086, collision self-report](../journal/2026/2026-10-12-raid-1084-1086-detached-gaze-occupancy.md)
- [Raid 1091/1092](../journal/2026/2026-10-13-raid-1091-1092-and-gaze-1374.md) and [PR 1374 merge](../journal/2026/2026-10-13-pr1374-author-scope-revision-and-merge.md)
- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
