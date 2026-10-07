# CI and the test suite

Scope: measurements and author decisions about the forge CI, the local CI
runner and the test suite's cost, 2026-10-02 to 2026-10-07. Standing
procedure lives in `skills/merge/SKILL.md` (where the local CI runs) and in
ticket 1045 (local merge gate, open); this topic records evidence only.

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
[2026-10-07 dream](../dreams/2026-10-07-second-dream.md)); it agrees with the
event and adds no rule here. Forge-check waits twice returned on a stale
rollup before the new head's checks existed (2026-10-06).

## Author decisions recorded in the sources

No `pre-push` hook calling the local runner. Ticket 1045: a local merge gate
replaces the forge's required checks after a review of the CI's content.
"Run the local CI on padme when it is reachable" was placed in
`skills/merge/SKILL.md` after the resident-rules budget test refused it in
`rules/git.md`.

## Sources

- [Suite economics](../journal/2026/2026-10-02-session-suite-economics.md)
- [Hunt 0875 runner nondeterminism](../journal/2026/2026-10-02-hunt-0875-runner-nondeterministic-guard.md)
- [Raid 1015](../journal/2026/2026-10-02-raid-1015-annotation-collision.md)
- [Local CI and act equivalence](../journal/2026/2026-10-06-local-ci-act-equivalence.md)
- [Leftover podman service](../journal/2026/2026-10-06-leftover-podman-service.md)
- [0913 close path, stale-base CI](../journal/2026/2026-10-06-0913-dispatch-close-path.md)
- [PR #1245 stuck check](../journal/2026/2026-10-07-pr1245-forced-gaze-stuck-ci-merge.md)
- Provenance: [source inventory](../../docs/memory-v8/source-inventory.md);
  revisions in [source-revisions.tsv](../../docs/memory-v8/source-revisions.tsv).
