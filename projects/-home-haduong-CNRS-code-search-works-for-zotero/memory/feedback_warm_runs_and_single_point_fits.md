---
name: feedback-warm-runs-and-single-point-fits
description: A cold benchmark run hides the download inside the measured window; a predictor fitted on one point matches it perfectly and proves nothing
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 6d719795-0c38-4d32-bd8a-400444db9509
  modified: 2026-08-29T14:02:05.863Z
---

Two errors compounded into a confident wrong mechanism, 2026-08-29, benchmarking
embedder resident memory.

**A cold run measures the download, not the thing.** RSS taken on a model's first
load read 364,8 MB where the warm run read 410,2, and 453,5 where warm read
404,9 — 45 to 49 MB of error, in *both* directions, so it does not even bias
consistently. That was larger than the 11,7 MB difference the numbers were being
used to argue about. Download first, then measure. Warm, over five fresh
processes, the spread falls to 2,5–6,9 MB, so a warm figure is good to about
10 MB and any ranking turning on less is noise.

**A fit calibrated on one point will match that point exactly and tell you
nothing.** From the cold numbers I built a `vocab × dim + constant` predictor of
resident memory, tuned its constant on multilingual-e5-small, and it reproduced
e5-small to a tenth of a megabyte. That felt like confirmation. Its first
out-of-sample test missed by 106 MB. The mechanism I had asserted — vocabulary
sets the RAM floor, quantization cannot shrink it — had to be retracted from a
ratification ledger entry that already argued from it.

**How to apply:** before a benchmark number enters an argument, ask two things —
was the artifact already local when the clock started, and has this cell been run
more than once? Report the median and the spread, never a single reading. And a
model fitted on *n* points is only evidence at the *n+1*th; state the calibration
set beside the fit, and treat a perfect match on the calibration point as the
absence of a test rather than the presence of one. Related:
[[feedback_benchmark_harness_traps]], [[feedback_probe_needs_discriminating_control]],
[[feedback_verify_the_load_bearing_claim]].
