---
name: feedback_assert_on_written_artifact
description: "A column allowlist drops a computed field silently — assert on the file the script writes, never on the record it builds."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fa43f1a4-d3ce-4606-999a-f115508717f6
  modified: 2026-07-27T13:59:29.090Z
---

`pd.DataFrame(records, columns=[...])` *selects* the named columns. A field the
record builder computed but the list omits is discarded one line later, with no
error and no warning.

**Why:** ticket 0288/0347 (2026-07-27). `catalog_keydocs.build_record()`
derived `keywords_provenance` — the author's explicit 2026-07-22 disclosure
rule — and `main()` built its DataFrame with
`columns=WORKS_COLUMNS + ["abstract_provenance"]`. The field vanished. Result:
242 of 263 curated key documents carried keywords with no provenance,
`keywords_provenance` was empty for all 33,344 refined rows, and the
Zenodo-deposited codebook honestly documented a column the deposit never
filled. 41 tests passed over it for five days: they asserted on
`build_record()`'s returned dict, and the merge test on a synthetic DataFrame
that already had the column. Neither read the CSV the harvester writes.

**How to apply:**
- The oracle is the **written file**. Drive `main()` in the test, read the
  artifact back, and assert the field is both present and correct. The
  existing end-to-end test in that very class already did this for
  `abstract_provenance` and simply never got a sibling for `keywords`.
- Grep the shape when a projection bug appears: `pd.DataFrame(.*columns=`,
  `df = df[SOME_LIST]`, `reindex(columns=`). In this repo the sweep found four
  sibling harvesters with the identical construction and no live defect —
  none of them computes a field outside `WORKS_COLUMNS`. Reachability, not
  shape, decides whether an instance is real.
- Watch **coupled allowlists**: a new per-source field must be added both to
  the emitter's `columns=` and to `catalog_merge.EXTRA_CARRY_COLS`, or it is
  dropped at whichever layer forgot. Two lists that must agree, with nothing
  enforcing it, is the latent half of this bug.
- Same family as [[feedback_render_oracle_for_generated_markup]] — test the
  artifact you ship, not the intermediate representation — but a different
  mechanism: no renderer is involved, the field never reaches the file at all.
