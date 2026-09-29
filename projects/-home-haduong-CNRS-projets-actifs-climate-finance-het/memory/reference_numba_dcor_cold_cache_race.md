---
name: reference_numba_dcor_cold_cache_race
description: Parallel pytest on an empty numba cache aborts dcor tests with "LLVM ERROR: Symbol not found" / SIGABRT; fixed by a serial `import dcor` pre-warm (PR #1571)
metadata:
  type: reference
  modified: 2026-09-29T16:15:46.128Z
---

**Symptom:** on a fresh environment, `make check` with 16 workers fails about 20 dcor/S2_energy tests (test_divergence, test_bias_flag, test_golden_values, test_embedding_sensitivity, test_null_model, test_subsampling_ribbon) with `LLVM ERROR: Symbol not found: __gufunc__...`, SIGABRT, crashed workers. A rerun often passes.

**Mechanism** (measured 2026-09-29): `dcor/_fast_dcov_avl.py:563-595` builds two gufuncs (cpu and parallel) from one function, both `cache=True`, compiled at import. numba's cache key omits the target, so concurrent writers on an empty cache leave mismatched files. The failure rate grows with the number of writers: 2 workers are enough. It reproduces without pytest, with 16 concurrent `import dcor`. Damage sometimes persists in the cache. With `NUMBA_CACHE_DIR` unset, the cache is per worktree venv (`<worktree>/.venv/.../dcor/__pycache__`).

**Fix in place:** the `numba-prewarm` make target, run serially before `check` and the six WP gates (ticket 1372). Not covered: pipeline runs that import dcor lazily under `make -j` (`scripts/_divergence_semantic.py`, `_permutation_semantic.py`, `divergence.mk` null-model). A cold-cache `make -j4` can still abort, loudly. Remedy: run `python -c "import dcor"` once first.
