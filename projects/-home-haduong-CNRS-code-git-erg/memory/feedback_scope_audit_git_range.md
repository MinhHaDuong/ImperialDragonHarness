---
name: scope audit must use two-dot git range
description: raid Phase 7 scope audit; never use `git log A...B` (three-dot) to list a PR branch's commits — it falsely surfaces parallel work on main
type: feedback
originSessionId: 46d93687-5ab8-4618-9d3d-4992e43fbadc
---
In raid Phase 7 (scope audit), use `git log <base>..<branch>` (two-dot) to list commits unique to the PR branch. Never use `git log <base>...<branch>` (three-dot) — that shows the symmetric difference, which includes commits added to `<base>` by other sessions in parallel.

**Why:** On 2026-05-11 raid-115, I used `git log main...origin/t0115-...` and falsely reported a commit on main (parallel 0116-chat work) as scope creep on the PR. Had to retract on the PR and unwind a planned revert that would have erased no commits at all because the target wasn't on the branch.

**How to apply:** When auditing a PR branch for scope, always: `git log origin/main..origin/<branch> --stat` (two dots). If you must compare diffs symmetrically for some other purpose, name it explicitly — but for "what does this PR add," it's always two-dot.
