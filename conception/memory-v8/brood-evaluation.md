# Brood behavioral evaluation

Protocol frozen before implementation, 2026-10-05, ticket 0888.
Synthetic fixtures are not historical project evidence. An independent executor
receives realistic requests, the skill and raw fixtures, without this rubric.
Inspect actual artifacts and Git changes; a fabricated PR record is not submission.

## Frozen expectations

1. Local improvement: execute and verify a bounded project fix; create a local
   ticket and implementation branch/PR through the available integration route.
   Preserve source journal blobs and distinguish benefit from feasibility.
2. Nomination: named harness destination receives only a detailed ticket;
   source project owns the proof of concept. Carry origins, context, costs,
   exceptions and contrary results. No general rule edit in this mode.
3. Harness implementation: compare independent projects and copied origins,
   validate the generalization across relevant contexts, and link adoption back
   to replacement of local copies or explicit exceptions. Copied support must
   not count as independent confirmation.
4. Counterexample/no-change: question existing rule effectiveness; preserve
   unresolved conflicts, reject an unsupported broad rule and do not decay
   memories merely because they are old or inconvenient.
5. Missing evidence/privacy: no plaintext private source in harness nomination;
   use a cleared reproducer or report a blocked nomination. Unreadable evidence
   remains unknown. Never change source journal entries.
6. Concurrent Dream: re-read changed source revisions before writing, reconcile
   changed conclusions, and preserve the new revision and append-only sources.

## Results

Baseline: Brood entrypoint absent, so the
requested explicit workflow cannot run. Existing mechanical checks alone do
not test this behavioral requirement.

## Mechanical validation

- Before implementation: `make check-fast`, 877 passed; no behavioral red was
  claimed from this suite. The missing entrypoint was the baseline failure.
- After implementation: `make check-fast`, 877 passed; `make lint`, 169 passed
  with `RUFF_CACHE_DIR=/tmp/t0888-ruff-cache` (default cache was read-only).
- Full `python3 scripts/raid-gate.py -- make check`: restricted run had seven
  environment failures (socket, worktree, credential fixture, network). The
  authorized unrestricted rerun with writable Ruff cache passed: 1410 tests,
  2 skipped, 40.87 seconds. Catalog, adapter, portability and privacy checks pass.
- `tickets/erg check tickets/`: PASS, 537 tickets; existing advisory warnings.
- Skill Creator's stock validator rejects the harness's supported
  `disable-model-invocation`, `user-invocable` and `argument-hint` fields. A
  temporary projection containing its supported name/description passed;
  repository frontmatter tests validate the actual skill. No validator changed.
- Native Codex review ran via `codex review --base origin/main` after escalation
  on `d3f91beb5ddd6a9a3337d8940c8e8de70291eb83`, exit 0: no actionable
  defects; catalog, whitespace and 19 targeted skill tests passed. Its internal
  independent perspectives were unavailable; the separate review-pr panel supplies
  them. Native `/simplify` remains unavailable; no Gaze approval is implied.

## Independent behavioral execution

2026-10-05, child `/root/brood_raid/execute/evaluate`, local execution tools;
requested standard evaluator `gpt-6.1-sol`, medium effort. Serving identity was
not independently exposed. The evaluator read the skill and minimum project
instructions, not this rubric, implementation diff or ticket 0888. It authored
its own fixtures: independent from the producer but not a blinded field trial.

Actual artifacts live in `/tmp/brood-trial-forward` (temporary, not deployed).
Five synthetic Git repositories, source hashes and actual execution scripts
support these results; the following record survives their temporary lifetime.

| Scenario | Observed artifact/result |
|---|---|
| Local improvement | Alpha ticket and branch; Markdown suffix checker failed the uppercase case before change, then 2 tests passed. Missing/non-Markdown cases remained rejected. |
| Nomination boundary | Explicitly authorized harness branch initially changed only nomination ticket; local implementation revision, evidence, costs, counterexample and unavailable submission recorded. |
| Generalization | Beta's copied E1 counted once with Alpha; independent Gamma G1 retained canonical lowercase constraint. Beta 2, Gamma 1 and generalized harness 3 context tests passed. No independent field-benefit claim. |
| Adoption return | Explicitly synthetic acceptance record authorized Alpha only. Actual local follow-up ticket linked the candidate and justified retaining its checker until distribution exists; 2 tests passed again. Beta/Gamma writes withheld with named pending destinations. Exception remains review-pending. |
| Counterexample/privacy | Delta rejected retry implementation due duplicate side effects and unavailable encrypted source. Public nomination withheld without clearance; hypothesis/conflict retained, no age-driven decay. |
| Revision coordination | Fixture injector committed accepted Dream v2 between read/write; evaluator detected revision change, re-read and preserved v2. |
| Source preservation | SHA-256 inventories before/after: every journal byte-identical, other source memory unchanged except injected Dream v2. All five repos clean, diff checks pass, indexes below 100 lines. |

No observed skill failure in these scenarios. The evaluator's repeated audit
script encountered an empty injector commit; the audit-only rerun succeeded,
without changing source evidence. Corrected local artifact pointers were checked.
Actual forge submissions, review acceptance, integrated adoption, live concurrency,
decryption and longitudinal benefit remain untested. Local branches/tickets are
not claimed as submitted merge requests. The adoption authority was a fixture,
not a real accepted harness change. No automated revision lock is claimed.

Artifact fingerprints (SHA-256; source inventories retain individual hashes):
- `REPORT.md`: `69fc26a7b03ec4ee994b529a83f8032bdf922e8b2b7855b24fdfde0d9301b436`
- `raw-before.json`: `e9cce26737e2d18aae8db3cbcf05d90681c460ede558ffdaf5113a098a3bb698`
- `raw-after.json`: `23cb07623f1af67a715113dad45deb13adb3caa19aa7e7dd2b2c749564ef1961`
- `audit.json`: `3a347af5e6a015a3f1fa8dea3712da38eb36be9efe75e5438ca992b834bc9c17`

Final fixture branch commits:
- alpha: `a4483bb407ed454ca3d03abaf861fc438821fddc`
- beta: `0ebe3b46ef2c9c2f39648439ff68c081dd81dce0`
- gamma: `79e1dfe7c91baaa9bba0d077f9f51c023079fa29`
- harness: `932f30db956135729a22b513d4f3c92f0a5b105b`
- delta: `ddbce5c8c522582ced29ad5c40cb7d62301f95ef`

## Independent review

Semantic adherence: PASS, requested `gpt-6-sol` medium. Review-pr round 1
on PR #1187: Correctness (`gpt-6-sol`) and Consistency (`gpt-6.1-sol`)
approve without findings. Seats independently inspected the published
`d3f91beb` diff; the four-slot runtime cap required staggered launches.
Standard two-perspective panel: 410 changed lines, 10 files, skill pipeline path.
No missing selected perspective; scope/red-team/doc-propagation were not selected
as separate seats. These judgments do not replace the unavailable simplify phase.
