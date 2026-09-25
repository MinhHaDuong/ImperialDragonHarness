---
name: feedback_fresh_worktree_failures_are_not_main_red
description: A failing test in a fresh worktree is not evidence that main is red until its error names something other than missing data or file-date order
metadata:
  type: feedback
---

On 2026-09-25 I told the author "check-fast shows 6 failures on main"; all six
were `FileNotFoundError` under `data/jetp/documents/objects/` because the fresh
worktree never ran `make jetp-data`. Earlier the same day, two corpus freshness
failures came from `dvc checkout --force` writing files a few ms apart. Only
the four country-migration failures were real (ticket 0940, already filed).

**Why:** a red main is a broadcast that makes parallel sessions race to fix it;
a false alarm costs everyone.

**How to apply:** before saying "main is red", read one error per failing
group. Missing data under `data/`, or an mtime comparison after a fresh
checkout, is a setup artifact; say so. Then check `tickets/` on `origin/main`
for an existing ticket before proposing one. Related:
[[reference_machine_padme]], [[feedback_worktree_make_check_corpus]].
