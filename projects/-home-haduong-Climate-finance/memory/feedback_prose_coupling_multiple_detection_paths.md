---
name: feedback_prose_coupling_multiple_detection_paths
description: "Grepping prose for an artifact's quoted numbers finds only one of the ways an artifact can be prose-coupled — check guards, producer scripts, freeze claims, and Makefile pairings too"
metadata:
  node_type: memory
  type: feedback
  originSessionId: f6a59d05-fc03-4ef4-8906-2e4ae1c5323b
  modified: 2026-07-28T20:31:42.594Z
---

Ticket 0641's regeneration audit rebuilt all 63 git-tracked Phase-2 artifacts
against the pinned `dvc.lock` corpus and found 5 substantive movers. Grepping
the citing prose for each artifact's numbers found none of the four coupled
ones — each was caught by a different mechanism instead:

1. `tab_null_separation_pre2007.csv` — a **failing test guard**
   (`test_a5_prose_matches_committed_csv`) that reads six figures out of the
   CSV and asserts each appears in the manuscript bullet.
2. `fig_breaks.png` — a **hardcoded threshold and marker label** in the
   plotting script (`plot_fig2_breaks.py` draws the z=1.5 significance line
   and labels 2015/2021 "not a break"); the regenerated figure put the 2015
   marker past its own script's threshold.
3. `fig_bars_v1.png` — an **explicit freeze claim in prose**
   (`manuscript.qmd` A.2 says the figure is "frozen on the corpus as it stood
   at the first submission") that the producer script does not actually
   honor (`plot_fig1_bars.py --v1-only` filters the live `in_v1` column).
4. `tab_pre2007_coverage.csv` — a **Makefile pairing plus a producer
   docstring** (`separation.mk` declares `separation: $(SEP_COVERAGE)
   $(SEP_NULL)` as one rule; the docstring says the numbers "decide the
   interpretive regime" jointly with the null-separation CSV above).

When auditing whether a regenerated artifact is safe to commit alone, check
all four surfaces — existing test guards, the producer script's own hardcoded
thresholds/labels, prose freeze claims, and Makefile prerequisite pairings —
not just a grep of the prose for the artifact's numbers. A regeneration audit
that commits nothing can still be the highest-value PR of the day: of 63
artifacts, 20 were proven reproducible, 37 had no producer, 1 was excluded by
author decision, and the 5 movers were each routed to author arbitration
(tickets 0670, 0671) rather than force-committed to make the audit look
complete — a lone commit on any of the four coupled ones would have broken
its pair.

Related: [[feedback_stale_prerequisite_masks_missing_artifact]],
[[feedback_vars_file_provenance]].
