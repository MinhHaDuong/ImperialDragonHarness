---
name: project-greedy-glob-class
description: "Colocated-output greedy-glob anti-pattern in exp1_batch2 consumers — guards, standing test, and the full instance list"
metadata: 
  node_type: memory
  type: project
  originSessionId: 802c1288-8566-4d8b-aed5-f93318879d00
---

The exp1_batch2 run dir is globbed by several consumers that parse
`<model>-run<N>.csv` with greedy `^(?P<model>.+)-run(?P<run>\d+)\.csv$`. Without
a prefix skip, colocated `reconciliation_*-run<N>.csv` / `filtered_*-run<N>.csv`
outputs are captured as spurious "models" (e.g. 140 rows instead of 70).

**Canonical guard:** `_SKIP_PREFIXES = ("reconciliation_", "filtered_")` then
`if any(name.startswith(p) for p in _SKIP_PREFIXES): continue` BEFORE the
parse. Pattern lives in `tabulate_coherence.py`. **The real artifact names**
(verified 2026-06-09): `reconciliation_*` is a PREFIX (match_type schema, NO
`source_1`); the real "filtered" output is `*_filtered.csv`, a SUFFIX written by
`query_verification` (`{stem}.csv` + `{stem}_filtered.csv` into the SAME dir),
and it RETAINS `source_1`. The `filtered_` PREFIX matches no current file —
kept defensively only. A content-filter on `source_1` excludes reconciliation
but NOT `*_filtered.csv`; that needs `_SKIP_SUFFIXES = ("_filtered.csv",)`.

**Standing test:** `tests/test_no_colocated_output_leak.py` (ticket 0496,
`@pytest.mark.adherence`) seeds genuine + decoy CSVs against each registered
consumer and asserts decoys are ignored. Add new consumers to its registry.

**Instances (all GUARDED + tested as of 2026-06-09, class CLOSED):**
- `score_exp1.py` (0495), `screen_validation_within_model.py`
  (only skipped `reconciliation_` until 0496 added `filtered_`),
  `tabulate_coherence.py`, `test_score_mechanical.py` (0492 test path).
- `scripts/audit_lp_mismatched.py` + `score_provenance.py` (0499): both now skip
  prefix AND `_filtered.csv` suffix. `score_provenance` uses a CONTENT filter
  (`_has_provenance_columns`) that misses `*_filtered.csv` (retains `source_1`);
  `audit_lp_mismatched` was safe-by-accident vs reconciliation only because
  `load_plants_csv` returns `[]` for that schema. (`scripts` is a package →
  importable in the standing test.)
- NOT the anti-pattern (intentional `reconciliation_*` globs):
  `tabulate_decomposition_fix.py` (frozen, 0424), `sweep_matching_threshold.py`.

**Lessons:** (1) the standing class test caught a live `filtered_` gap in
screen_validation on its FIRST run, and the roar sweep found 2 more instances —
the class was broader than the 4 originally enumerated. (2) **Verify the real
artifact name against the WRITER, not the ticket premise** — both 0499 ticket
prose and a prefix-only first pass guessed `filtered_` prefix; the advisor
caught that the real file is the `_filtered.csv` suffix, and a prefix-only skip
would have "protected" a fictional file while the real one leaked. (3) When a
decoy reuses a genuine model name (`X-run1_filtered.csv` → model `X`), assert on
`(model, run)` pairs, not just models, or the leak test is toothless. See
[[feedback-ticket-premises-are-hypotheses]] and [[feedback-make-stamp-discipline]].
