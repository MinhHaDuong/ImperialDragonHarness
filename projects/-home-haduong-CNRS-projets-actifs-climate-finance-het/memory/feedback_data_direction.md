---
name: Data flows padme→doudou only
description: Never push data/DVC from doudou to padme. Padme is the data authority.
type: feedback
---

Never push data or DVC outputs from doudou to padme. Data flows one way: padme→doudou.

**Why:** Pushing doudou's pool to padme caused hours of reprocessing and drift (2026-03-17). The machines had slightly different pool contents, different caches, and different dvc.lock states. Resolving the mess took longer than the original pipeline run.

**How to apply:** `dvc push` only on padme, `dvc pull --force` only on doudou. If doudou finds new data (e.g., OpenAlex queries), commit the query config change and let padme re-collect from scratch — don't scp data files between machines.
