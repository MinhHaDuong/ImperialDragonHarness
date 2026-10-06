# Local CI replacing the forge's: what was measured and decided (2026-10-05/06)

Context: on 2026-10-05 the forge's hosted runners stopped being provisioned
(status page: Actions degraded; every PR's CI sat `queued` from about 19:20 UTC).
Runs resumed by 2026-10-06 03:00 UTC. The author's direction: first a local CI
with checks exactly equivalent to the forge's, then a separate reflection on
whether its content duplicates or misses guarantees; longer horizon, a CI native
to git for the dyne project.

Merged: PR 1218 (runner, `1aaf71ec`), PR 1229 (ticket 1045 and a draft spec,
`77d05036`), PR 1230 (where the local CI runs, `3f9ec63d`), PR 1231 (ticket 1045
corrected, `b6d391d6`). Ticket 1041 (runner) is closed in the wrap-up of this
entry; ticket 1045 (local merge gate) is open.

## Measured

- `CI.yml` has 10 jobs on `ubuntu-latest`. `make check` is not equivalent to it:
  it lacks `validate-tickets`, `status-verb-guard`, `pipefail-guard`,
  `grep-e-guard`, `tab-ifs-guard` and the in-line self-tests, and includes
  `check-skills-drift` and `check-adapter-hooks`, which CI does not run.
- `act` 0.2.89 runs the unmodified workflow under rootless podman. `act -j`
  honours only the last `-j` (a grouped call silently ran one job); act's default
  checkout copy drops `.git` (22 tests failed, `--bind` on a real clone fixed
  it); the stock image runs as root without podman (3 failures, 18 skips). A
  custom image (non-root uid 1000, podman, `gh`, passwordless sudo, pip-writable
  system Python, a dedicated podman service with `keep-id`) matches the forge.
- Parity on commit `715c59d7`: the same 10 jobs, 1487 passed and 10 skipped on
  both sides; `grep` 3.11, `bash` 5.2.21, GNU Awk 5.2.1. On an earlier head of PR
  1218 the forge and the runner failed the same two jobs: agnostic-guard (the
  negative-controls script held the forbidden consumer path literally) and
  pytest-guard (the same two tests: agnostic on scripts, and the marker-hygiene
  ratchet for a test that spawns a subprocess).
- Negative controls: one injected violation per guard in a throwaway clone; the 9
  guarded jobs each failed at their own step (three solo series, 9 of 9). The
  first series reported 9 "caught" while no job had run: the podman socket path
  exceeded the ~108-byte unix socket limit. A later series showed an
  infrastructure failure on personal-data-guard while a second runner shared the
  host; the log was lost and the cause is not established.
- `cross-pr-ticket-collision`: it first passed vacuously ("this PR adds no
  ticket files"). An earlier statement in this session, that the sibling-PR path
  had run without warning, was wrong: the base-ref collision fired before the
  script reaches `gh`, and the custom image then lacked `gh` (exit 127). The
  sibling-PR path fired as a true positive ("ticket ID 1041 is also added by open
  PR #1218") when the runner did not recognise its own PR, because the local
  branch was named differently from the pushed one; the runner now finds its PR
  by the HEAD sha.
- Forge optional: with no `origin`, `gh` or login, jobs that read `secrets.*` are
  skipped and listed in the summary (a skip is never a pass; `LOCAL_CI_STRICT=1`
  makes it fail). No workflow at HEAD exits 3; a job set that differs from the
  workflow's, or an unknown job name, exits 2. Checked in throwaway repositories.
- Review of the runner (gpt-6.1-sol, medium, read-only, before the first commit;
  see the attribution entry for PR 1218). Findings: a zero-job discovery can exit
  0; the clone is of HEAD; base ref hardcoded to `main`; the user's forge token
  goes to the jobs; one shared writable clone; no timeout or signal cleanup; image
  never rebuilt; the new `ci-local/` files are excluded by the repository's
  catch-all ignore rule. The token exposure is documented and accepted, the rest
  was changed or documented.

## Forge settings

- Ruleset `main-required-checks` on the default branch requires 7 checks
  (validate-tickets, skill-lint, agnostic-guard, status-verb-guard,
  pipefail-guard, grep-e-guard, pytest-guard), with no bypass actor. Three CI jobs
  run but are not required: personal-data-guard, tab-ifs-guard,
  cross-pr-ticket-collision.
- A bypass actor (repository admin role, mode `pull_request`) was added on the
  author's request after a merge, then removed at the author's request ("I would
  rather wait than bypass"); both changes were read back from the forge. The
  ruleset is as it was before.

## Decisions by the author

- A `pre-push` hook calling the local runner is not wanted.
- Ticket 1045: a local merge gate replaces the forge's required checks, after a
  review of the CI's content. Trust is a base principle of IDH: no open door.
  Traceability means tracing agents that get around the CI with git options
  (`--no-verify`, `core.hooksPath`, `update-ref`, `branch -f`, `push --force`, a
  ruleset edit), with no dependence on one agent runtime. My first reading, who
  ran the CI, was wrong; the runner's output line (UTC time, actor, host) stays.
- "Run the local CI on padme when it is reachable" is a rule. It went first into
  `rules/git.md`; `tests/test_rules_resident_budget.py` refused it (18130 chars
  against 17800). It is in `skills/merge/SKILL.md` (section "Before merging"),
  with the fallback "run where you are and name the host". The cap is unchanged.
- This host reports 24 threads (12 cores); a 32-core upgrade is ordered, not
  delivered.

## Process facts

- `commit --no-verify` was used in throwaway clones (probe commits that inject a
  violation), and the negative-controls script does so in its own clone; never on
  a repository branch.
- A `--force-with-lease` was first issued with a SHA completed from memory; git
  rejected it ("stale info") and nothing was overwritten; it was redone with the
  SHA read from the remote.
- The wait for the forge's checks twice returned before the new commit's checks
  existed (a stale rollup); it now requires the expected head sha and 10 checks.
- Ticket 1045's "created" log time (08:45Z) was estimated and is later than the
  real creation; the log is append-only, so a note records it.

## Environment of Claude Code on the web (from its documentation, not tested)

Fetched 2026-10-06 from code.claude.com/docs/en/cloud-environments and
claude-code-on-the-web: a fresh Ubuntu 24.04 VM per session (4 vCPU, 16 GB, 30 GB
disk); Docker preinstalled; podman, rootless and nested containers not
documented; network default "Trusted" (github.com, container registries, PyPI;
`cli.github.com` absent from the list); `gh`, `uv`, `jq`, `yq` preinstalled, `act`
and `age` not; a root setup script with a filesystem cache; foreground commands
default 2 min, max 10 min; git hooks and worktrees not documented. Whether `act`
works there is untested.

## Survey and open items

- Eight projects were surveyed by a cheap agent; three have a forge CI to replace.
  That survey miscounted the harness's own CI jobs (3 instead of 10).
- Open: ticket 1045 and its prerequisite, the review of the CI's content.
