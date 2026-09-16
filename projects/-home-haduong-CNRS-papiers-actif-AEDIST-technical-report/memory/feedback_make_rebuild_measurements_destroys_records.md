---
name: make-rebuild-measurements-destroys-records
description: "`make rebuild-measurements` deletes ALL .record.json across outputs/ and derived/ before regenerating — destroys baseline cohort records if a downstream target fails mid-build."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de20a516-38a3-4ccc-b4a4-236f555d39aa
---

`experiments/Makefile`'s `rebuild-measurements` target runs:
```
find outputs derived -name '*.record.json' ! -path '*/_extracted/*' -delete
$(MAKE) ../measurements.jsonl
```

If the second step fails (e.g. it depends on `../.env` which is missing
in a fresh worktree), you're left with zero .record.json files. The
.csv inputs survive, so a full re-eval can rebuild — but evaluation is
not free, and an interrupted rebuild loses all cohort records silently.

**Why:** Hit while building ticket 0198 — the rebuild's downstream
self-consistency step failed on missing `../.env` and left both the
2026-05-20 baseline cohort and the new 2026-05-21 topup cohort without
record.json files. Recovery required `git checkout HEAD -- outputs/` to
restore baseline, then re-running evaluate per-csv for both cohorts.

**How to apply:** Don't run `make rebuild-measurements` unless you've
confirmed `../.env` exists and all downstream targets resolve. For
adding a single new directory's records, run `extract` + `evaluate`
directly per-csv, then call `aedist.evaluate assemble` on the union of
ALL existing .record.json files to refresh measurements.jsonl — don't
rely on the Makefile's destructive prepass.

Long-term fix: `rebuild-measurements` should either be transactional
(stage-then-replace) or scoped to a single cohort.

**2026-06-06 update (v2.1 re-score):** worse than mid-build failure — even a
SUCCESSFUL rebuild cannot reproduce the committed mart: (1) census-era records
are restorable-only (raw replies archived, 0422) so regeneration yields ~108 of
562 rows; (2) restoring them BEFORE assemble pollutes the mart +149 rows (the
101 Exp2 turn records are created AFTER mart assembly in canonical ordering and
must be absent at assemble time); (3) `reconciliation_*.csv` transients left in
outputs/exp1_batch2 by evaluate poison `score_exp1`'s filename glob (140 rows
instead of 70). A reference flip = surgical row replacement in the committed
mart (match by result_file, replace only re-scored rows), never a fresh
assemble. Full protocol: gate doc `data/reference/extensions_standalone_vs_absorbed.md`.
