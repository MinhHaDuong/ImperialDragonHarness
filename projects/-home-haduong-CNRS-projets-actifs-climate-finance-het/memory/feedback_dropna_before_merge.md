---
name: Drop nulls before pandas merge on DOI
description: Pandas merge(on=col) matches NaN==NaN, causing cartesian explosion with null DOIs in corpus data
type: feedback
originSessionId: 33ed9475-a4cc-4f5d-80dd-7bd8fc563ec5
---
Always `dropna(subset=[col])` before `merge(on=col)` or `set_index(col)` when the column may contain nulls.

**Why:** refined_works.csv has ~7.7K null DOIs; other catalogs have similar counts. Pandas treats NaN == NaN in merge, producing N×M rows (60M from 31K). This OOM-killed padme twice at 105GB RSS before diagnosis.

**How to apply:** Any new script that merges on "doi" or sets it as index must drop nulls first. Grep for `.merge(` and `.set_index("doi")` in review.

**Merged from `feedback_or_empty_does_not_catch_nan.md` (2026-09-25):** str(x or "") and row.get(k, "") return 'nan' for a pandas NaN (truthy, key present); blank on pd.isna(v) once per function; grep shipped artifacts for \bnan\b.
