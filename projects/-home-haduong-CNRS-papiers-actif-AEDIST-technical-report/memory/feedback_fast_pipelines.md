---
name: Fast pipelines — no waiting
description: Evaluate/summarize should be instant, not minutes of logging noise
type: feedback
---

Reading JSON files and tabulating results should be instant. The evaluate pipeline is too slow because it logs every cleaning step and the MILP solver runs per-model. The user expects sub-second feedback for batch operations on local data.

**Why:** The user's time is the bottleneck, not CPU. Noisy logging (every diacritic strip, every pattern match) makes it hard to see actual results.

**How to apply:** Set logging to WARNING by default in batch operations. Only INFO for headlines (model name, F1 score). Profile if evaluation takes >5s for 100 files — the cleaner and MILP solver may need caching or vectorization.
