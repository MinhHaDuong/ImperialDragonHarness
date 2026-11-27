# Source and scenario audit for ticket 1576

Documentation/source verification only, 2026-11-27; no numerical reruns.

## Source check

Inspected official Release 19 manual entries, copyright 2025: generate pages
1, 2, and 5; egen syntax and std() example page 15; User's guide sections
13.2.1 and 13.7; gmm pages 2, 5–7, and 13–15; xtgee page 4 and correlation
structures pages 17–18 (including PDF page images for formulas). The links
and limits are recorded in references/stata-caveats.md. StataCorp's Stata 11
FAQ explicitly excludes recent versions. This is documentary evidence; the
authors' historical installation/settings have not been established.

## Before/after scenario audit

| Scenario | Before | After |
|---|---|---|
| Translator treats replace as always retaining type | No generic correction of the proposed case recollection | Documented promotions and nopromote identified; float-to-double promotion not inferred |
| Package uses explicit double or set type | No shared storage caveat | Configurable generate storage and function-specific egen evidence retained |
| Panel translation treats x[k] as always within-panel or division by zero as infinity | No shared expression caveat | Current order/by scope and missing arithmetic documented |
| Cluster VCE is assumed to select a clustered second-step GMM weight | No shared distinction | Defaults documented separately; reverse implication explicitly documentary, historically unresolved |
| A fitted AR normalization or combined GEE correction is reused for every paper | No generic boundary | Case calibration separated from documented Gaussian robust rgf; historical factor remains open |
| No Stata licence and no translation authorization | No new route | Pointer grants no translation authorization or CRA ruling (negative control) |
| Explicit authorized translation with known options/version | Existing translation declaration/equivalence uncertainty | Can consult official evidence while retaining option/version record and validation freezes (positive control) |

Preservation check: unchanged assessment.md, rules.md, validation.md, and
Gavard mapping are byte-compared with base. Only a conditional reproduce
pointer is added to the skill; its scoring, tolerance, signing, and publication
steps remain unchanged. No wording-pinning tests are added.
