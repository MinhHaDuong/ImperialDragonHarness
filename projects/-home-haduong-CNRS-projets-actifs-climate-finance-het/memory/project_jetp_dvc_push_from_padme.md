---
name: project_jetp_dvc_push_from_padme
description: "JETP DVC objects produced on padme were never pushed to the remote until 2026-09-17; make jetp-data is cache-only (dvc checkout), so a fresh machine needs an explicit dvc pull first"
metadata: 
  node_type: memory
  type: project
  originSessionId: b5a60d4e-2e95-41b2-bf5c-51ffa295522e
  modified: 2026-09-17T17:02:03.332Z
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

**How to apply:** after any JETP session on padme that adds DVC outputs, end
with `dvc push` on padme (data flows padme → doudou, see
[[feedback_data_direction]]). When a replay test fails on doudou with a hash
mismatch or missing input, check `dvc status -c` on padme before suspecting
the data. Open defect seen the same day: `tests/test_jetp_public_release.py`
pins commit 3b432ef3, which exists only in padme's reflog, so it fails on any
clone.
