---
name: reference_jetp_preview_documents_refresh
description: "JETP observatory preview: make jetp-observatory-documents skips an existing documents/ dir, so newly collected sources 404 until copied in; doudou's shared .venv has no dvc"
metadata:
  node_type: memory
  type: reference
  originSessionId: 93dc4598-7818-4bb8-b7ae-fc2584b8e87b
  modified: 2026-09-24T13:10:00.362Z
---

`make jetp-observatory-documents` exits 0 without work when
`deliverables/jetp-observatory/documents` already exists, so sources collected
after the first copy stay missing from the preview (2026-09-24 on doudou: 2 of
266 Viet Nam links 404'd, both collected 2026-09-22). Refresh with
`make jetp-observatory-refresh` (restages the whole copy); since PR #1485 the documents target prints a warning when the copy is stale.

On doudou the shared `.venv` has no `dvc`, so `make jetp-data` fails in a fresh
worktree; use padme for a clean build, or doudou's primary checkout, whose
`data/jetp/documents` is already populated. The author previews the observatory on
port 8765 from the primary checkout. Full check:
`.venv/bin/python tests/browser/jetp_observatory.py --url http://127.0.0.1:8765`.

Related: [[project_jetp_dvc_push_from_padme]], [[project_jetp_three_stages_m1a]].
