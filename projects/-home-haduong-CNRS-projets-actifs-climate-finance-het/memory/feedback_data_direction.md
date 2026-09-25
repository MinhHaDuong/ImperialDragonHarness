---
name: Data flows padme→doudou only
description: Never push data/DVC from doudou to padme. Padme is the data authority.
type: feedback
---

Never push data or DVC outputs from doudou to padme. Data flows one way: padme→doudou.

**Why:** Pushing doudou's pool to padme caused hours of reprocessing and drift (2026-03-17). The machines had slightly different pool contents, different caches, and different dvc.lock states. Resolving the mess took longer than the original pipeline run.

**How to apply:** `dvc push` only on padme, `dvc pull --force` only on doudou. If doudou finds new data (e.g., OpenAlex queries), commit the query config change and let padme re-collect from scratch — don't scp data files between machines.

**Merged from `feedback_make_corpus.md` (2026-09-25):** Say make corpus (padme: dvc repro + push) or make corpus-sync (doudou), never bare dvc repro, which skips the push.

**Merged from `project_jetp_dvc_push_from_padme.md` (2026-09-25):** After a JETP session on padme that adds DVC outputs, dvc push there; a fresh clone needs dvc pull data/jetp/documents.dvc (and data/jetp/crs) before make jetp-data, which is cache-only. Capturing new documents from a padme worktree: point cache.dir at the primary's cache, restore missing tracked objects from the .dir manifest before dvc add, then make jetp-documents-track + dvc push.
