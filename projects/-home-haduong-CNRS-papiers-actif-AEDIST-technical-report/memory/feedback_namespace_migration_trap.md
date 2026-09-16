---
name: feedback-namespace-migration-trap
description: In-place jsonl migrations leave source .record.json files stale — every future rebuild silently reverts the migration
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f4537f72-6ba0-4e22-b885-a15b15f10ed9
---

When migrating measurements.jsonl to new vocabulary (method names, prompt_version values), the source `.record.json` files on disk must be migrated TOO. Otherwise any future `make rebuild-measurements` walks those stale sources and silently reverts the migration.

**Why:** PR #286 (ticket 0120) migrated measurements.jsonl in place from `single`/`decomposed`/`frontier` etc. to the new `direct`/`rag`/`direct+multiturn` vocabulary, but never rewrote the 257 source .record.json files. PR #354 round 1 (the Exp 1 sweep) ran rebuild-measurements and the migration silently reverted — CI test `test_decomposed_deepseek_has_3_replicates` caught it. Fix took two PRs: round 1's "restore measurements.jsonl + append new rows only" (#354 fix commit) and a later proper migration of the source files (`scripts/migrate_record_json.py` in #362).

**How to apply:**
- For any in-place jsonl rewrite, also migrate the upstream sources or document the regression risk.
- `scripts/migrate_record_json.py` is the idempotent migrator for the 0120 vocabulary; pattern is reusable.
- When `aedist.evaluate assemble` produces a measurements.jsonl that differs from origin/main only on the field being migrated, treat that as the smoking gun — don't commit, restore origin/main and migrate sources first.
