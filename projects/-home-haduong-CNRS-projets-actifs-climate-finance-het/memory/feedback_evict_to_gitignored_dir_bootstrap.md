---
name: feedback_evict_to_gitignored_dir_bootstrap
description: Evicting a pipeline output from a git-tracked dir to a gitignored one removes the free dir-bootstrap — producers using validate_io must os.makedirs first.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 64204d5a-1630-4c3c-951c-028469088605
---

When moving a Phase-2 output from `content/tables/` (git-tracked, always present)
to a gitignored/regenerable dir like `data/derived/tables/` (`$(DERIVED)`), the
destination directory is NOT guaranteed to exist on a clean tree or under `make -j`.

**Why:** producers that write via `script_io_args.validate_io()` only *check* the
output dir exists (they `raise FileNotFoundError` if absent) — they do not create
it. `content/tables/` existed for free (tracked with deliverables), so the check
always passed. Pre-eviction, `analyze_bimodality` even *created* `data/derived/tables`
as a side effect because its `validate_io` target was `content/tables` and it later
`makedirs`'d `pole_dir=DERIVED`. Move the `validate_io` target itself to `$(DERIVED)`
and that bootstrap vanishes → "Output directory does not exist" on isolated/`-j` builds.

**How to apply:** every producer whose `--output` now lands in the gitignored dir must
`os.makedirs(os.path.dirname(io_args.output) or ".", exist_ok=True)` *before* `validate_io`
(don't change `validate_io` — its raise-on-missing-dir is pinned by
`test_io_discipline`). Check `import os` is present. Also: regression/test harnesses
with a tmp-isolation path whitelist (e.g. `compute_regression_hashes.py::_redirect_args`
matched only `content/`, `tests/`) must add the new `data/derived/` prefix, or they
write to the real tree and the existence check fails. Verify end-to-end: `rm -r
data/derived && make data/derived/tables/<file>` on a clean tree must succeed.

Ticket 0218 (eviction of 17 residual Phase-2 `tab_*` intermediates). Related:
[[feedback_verify_datadep_worktree_symlink]] (symlink primary's contract files to
build data-dependent targets in a worktree).
