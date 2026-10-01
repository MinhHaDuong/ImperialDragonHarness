# Legacy memory retirement

Author direction: “RETIRE LEGACY”, 2026-10-01. This supersedes deferring the
unused DREAM helpers until the broad rollout. It does not certify the pilot
or retire other projects' native memories.

## Removed execution paths

Removed `skills/dream/read-index.py`, `commit.py` and `provenance.py`.
They implemented native-profile reads, shared-store staging, cross-project
promotion candidates, provenance mutation and decay calculations. The merged
v8 DREAM skill already forbids calling these helpers and uses ordinary project
file reading, Git and reviewed reports. Missing project convention or DREAM.md
stops the invocation before mutation; no old-store fallback remains.

Consumer audit covered scripts, hooks, adapters, skills, CI and tests. Only
`tests/test_dream.py` and `tests/test_provenance_coverage.py` consumed the helpers;
those implementation-specific tests are removed with the implementation. No
runtime hook or adapter wiring needed replacement. A retirement regression
check prevents restoring those executable helpers accidentally. This audit is
repository-scoped; external callers receive a missing-file failure, and no
compatibility shim can reactivate legacy writes.

The active harness index no longer advertises rule promotion or links the
obsolete advice. The original advice stays visibly retired in its source file;
Git retains its earlier bytes. Legacy project exports, inactive notes, aliases,
provenance JSON and lock remain unchanged as historical evidence. Nothing scans
or mutates them through the retired helpers. The revision inventory records the
pre-retirement baseline, deliberately not a rewritten source history.

## Tickets and remaining delivery

0934 and 1002 are superseded by removal, not completed portability fixes. 0991's
EU scoring, tombstone purge and rule machinery are abandoned, not implemented.
0913 records this retirement batch but remains open for project-by-project
rollout, replacement evidence, audience checks and runtime limitations.
0920, 0988, 0916, 0910 and the behavioral evaluation remain separate work.
No timer, automatic promotion or rule proposals are introduced.

## Recovery and verification

Recover historical code from parent commit `a849070d` with `git show` for
inspection; reactivation requires an explicit new decision. Never restore it
as a fallback during DREAM. Source notes remain readable without these helpers.
Verification uses fast and adherence gates, catalog/adapter synchronization,
agnostic and personal-data checks, plus a clean diff check. No live runtime
behavior is claimed from repository tests alone.
