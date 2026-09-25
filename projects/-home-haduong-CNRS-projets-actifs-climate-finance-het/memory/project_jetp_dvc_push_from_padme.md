---
name: project_jetp_dvc_push_from_padme
description: "JETP DVC objects produced on padme were never pushed to the remote until 2026-09-17; make jetp-data is cache-only (dvc checkout), so a fresh machine needs an explicit dvc pull first"
metadata: 
  node_type: memory
  type: project
  originSessionId: b5a60d4e-2e95-41b2-bf5c-51ffa295522e
  modified: 2026-09-25T09:00:00.107Z
---

Found 2026-09-17: the M1a replay tests failed on doudou because
`data/jetp/releases/vnm-migration-0764.json` (DVC-tracked) existed only in
padme's working tree. `dvc status -c` on padme listed 44 unpushed JETP objects
(releases, audit-evidence, jetp-pilots). Pushed that day; cache and remote now
in sync.

`make jetp-data` runs `dvc checkout` on `documents.dvc` and the VNM release
pointer only: no network by design (`docs/jetp-storage.md`). On a machine
whose cache lacks the objects it fails with "missing files". Run
`uv run dvc pull data/jetp/documents.dvc data/jetp/releases/vnm-migration-0764.json.dvc`
once, then `make jetp-data` works. `data/jetp/crs` is a frozen dvc.yaml stage
output, pulled separately (`dvc pull data/jetp/crs`).

**Capturing new objects from a padme worktree (ticket 1010, 2026-09-25).**
padme's primary checkout may sit on someone's branch, so work in a detached
worktree: write `.dvc/config.local` with `cache.dir` = the primary's
`.dvc/cache` and the local remote url `/data/projets/dvc/oeconomia-climate-finance`,
symlink `.venv`. The worktree's `data/jetp/documents` arrives populated with
the primary's files (228 then), which were not the tracked set (219 of 266
tracked + 9 new): a plain `dvc add` would drop the missing tracked objects,
and `dvc checkout` refuses (or with `--force` deletes) the unsaved new ones.
Copy the missing objects from cache by the `.dir` manifest's md5s, re-hash,
then `make jetp-documents-track` + `dvc push`; bring `documents.dvc` back to
doudou by scp and commit there. Count dedups: a "new" object can share a
sha256 with a tracked one.

**Full `make check` belongs on padme.** On doudou the preflight refuses
(corpus not materialized, reranker cache `llm_relevance_cache.csv` absent,
CRS inputs missing). In a padme worktree at `origin/main`: `make data`,
`make jetp-data`, `make jetp-crs-data`, copy `data/catalogs/llm_relevance_cache.csv`
byte-identical from the primary, then `PYTEST_WORKERS=16 make check`
(2026-09-25: 3347 passed, 50 skipped, ~3 min).

**How to apply:** after any JETP session on padme that adds DVC outputs, end
with `dvc push` on padme (data flows padme → doudou, see
[[feedback_data_direction]]). When a replay test fails on doudou with a hash
mismatch or missing input, check `dvc status -c` on padme before suspecting
the data. Open defect seen the same day: `tests/test_jetp_public_release.py`
pins commit 3b432ef3, which exists only in padme's reflog, so it fails on any
clone.
