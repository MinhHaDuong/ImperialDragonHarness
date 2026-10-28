# After-merge red 1322 cleared without a code change

Date: 2026-10-28. Project: ImperialDragonHarness. PR #1913.

- `merge-gate.py run-after` on main tip a8f1ba24 (after PR #1904) recorded
  `pytest-guard fail(exit 2) 376.8s`, failing
  `tests/test_idh_lifecycle.py::test_symlinked_bashrc_is_rewritten_at_its_target`
  and `::test_install_is_idempotent_and_refuses_foreign_files`; ticket 1322 opened.
- The next after-merge record, on 3932d601, passed all six checks
  (`pytest-guard pass 79.7s`). The diff a8f1ba24..3932d601 touched only
  `scripts/runtime.py`, `scripts/runtime_launch.py`, `tests/test_runtime_launch.py`.
- `tests/test_idh_lifecycle.py` ran 39/39 green in a fresh worktree on 3932d601.
- Both failing tests spawn `idh` with `timeout=60`; the gate record keeps test
  ids but no failure text, so the cause was not established.
- Decision: ticket 1322 closed on the green record (PR #1913, merge 6b722d7d);
  no timeout change made.
