---
name: feedback_no_ci_local_merge_gate
description: "This repo has no CI — a PR's CLEAN mergeStateStatus means no conflicts, not tests passed; run make lint + check-fast locally before merging"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1f0da5ae-caed-4c21-a772-f5b1dfd84436
  modified: 2026-07-28T21:01:30.895Z
---

`climate-finance-het` has **no continuous integration**. There is no
`.github/workflows/` directory, and `gh pr checks <N>` reports "no checks
reported on the branch" for every PR. `statusCheckRollup` is an empty array.

So a PR showing `mergeable: MERGEABLE, mergeStateStatus: CLEAN` is asserting
**only that git can merge it without conflicts**. It says nothing about whether
the test suite passes. There is no red gate between a broken branch and main.

**Why:** the phrase "CI passes" is meaningless here, and treating a green
GitHub UI as a quality signal would let a red branch land. The project's own
`/verify` contract already forbids "CI passes" as exit-criterion evidence — this
is the mechanical reason why.

**How to apply:** before merging anything, run the local gates from the merged
result and report the actual counts:

- `make lint` — the adherence tier (ruff, hygiene, contracts). This is what
  `test_ruff_clean` guards; ~14 s.
- `make check-fast` — the fast tier; ~14 s under xdist.
- `make check` adds the slow/integration tiers. Its corpus-data failures on
  padme are **real, not expected** — see [[reference_machine_padme]].

Both fast gates together cost under a minute, so there is no excuse for
skipping them on a merge wave. On the 2026-07-27 six-PR wave they were the only
verification that existed (post-merge main: lint 167 passed / 3 skipped,
check-fast 1140 passed / 6 skipped).

**Update 2026-07-28:** the per-PR gate itself has since eased —
[[project_merge_gate_eased]] — to `make check-fast` + `make lint` only
(~40 s); the full `make check` above now runs ex post (`/lair` step 9 on
main) and pre-PR only when the diff touches the pipeline surface
(`scripts/`, `libs/`, `dvc.yaml`, Makefiles, slow/integration tests). The
core claim here — no CI, so a CLEAN `mergeStateStatus` says nothing about
tests — still holds; only the required local-gate set for a routine PR
narrowed.

Related: [[feedback_verify_contract]] (what counts as evidence),
[[feedback_merge_conflict_all_hunks]] (why a clean auto-merge still needs a
content grep), [[project_merge_gate_eased]] (the current narrowed gate).
