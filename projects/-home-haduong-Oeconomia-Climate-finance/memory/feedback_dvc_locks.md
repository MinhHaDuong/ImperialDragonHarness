---
name: DVC stale lock cleanup
description: DVC rwlock file accumulates dead PIDs from killed processes — check and clean before running pipeline
type: feedback
---

When DVC `repro` appears to hang, check `.dvc/tmp/rwlock` for stale PIDs from killed processes. DVC auto-cleanup is unreliable — dead PIDs block new runs silently.

**Why:** Four dead processes (from a 2-day-old Claude session and killed DVC runs) blocked `catalog_merge` for ~10 minutes before diagnosis.

**How to apply:** Before any `dvc repro`, run: `cat .dvc/tmp/rwlock | python -m json.tool` and check if listed PIDs are alive (`ps -p PID`). Remove stale entries with `rm .dvc/tmp/lock .dvc/tmp/rwlock`.
