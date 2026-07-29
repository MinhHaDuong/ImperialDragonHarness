---
name: feedback_run_the_chain_reveals_what_reading_code_cannot
description: "Ticket 0570's first-ever full build of the Z-series divergence chain surfaced two defects invisible to code review: a peak-year argmax computed over a wider table range than the figure/title actually plot, and a vars target missing its data prerequisites so a rebuilt table silently didn't rebuild the vars file"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f6a59d05-fc03-4ef4-8906-2e4ae1c5323b
  modified: 2026-07-28T18:12:43.485Z
---

Ticket 0570 (PR #1280, 2026-07-28) was the first time the Z-series
divergence tables (`tab_summary_{S2_energy,L1,G9_community}.csv`) were
actually built end to end for the multilayer technical report. Running the
real chain — not just reading the collector code — surfaced two defects that
a code review of `compute_vars.py` alone would not have caught:

**1. An argmax over the wrong range.** The peak-year collector took
`argmax` over the full summary table, which starts at 1993. The plotting
script (`plot_companion_zseries`) draws `set_xlim(year_min, year_max)` =
1998-2021, and the paper's own title says "1998-2021". The collector would
have published a peak year outside the range the paper's own figure and
title claim to cover — a number technically computed correctly from its
input, but from the wrong slice of it. Only running the actual numbers (real
argmax = 1996, outside 1998-2021) against the actually-plotted range exposed
the mismatch; the code alone reads as a plain argmax with nothing wrong in
isolation. Red-proved against the originating defect: pre-fix code returns
1993 on all three keys once you actually run it.

**2. A derived target missing its real prerequisites.** The vars file
depended on `tab_summary_*.csv` in effect but not in the Makefile's
prerequisite list, so regenerating those tables did not trigger a
regenerated vars file — the exact "Makefile truth: prerequisites and
targets must match each script's actual file reads and writes" rule
(AGENTS.md) violated silently. Only visible once someone rebuilt a table and
watched the vars file *not* change. Fixed with `$(wildcard)` entries
matching the list's existing idiom; sweeping the whole prerequisite list
caught a second instance (`_vars_ablation.py`) that had landed on `main`
with the same gap while this branch was still open.

**How to apply:** when a collector or Makefile target has never actually
been exercised against real produced data — because the data was previously
absent, stubbed, or a sentinel — treat "make it run once, for real" as part
of the fix, not a formality after the code looks right. Two defect classes
(a computed value drawn from the wrong slice of its input; a target with an
incomplete prerequisite list) both require the concrete execution to see,
and both would ship silently at exit 0 if the sentinel fallback were simply
replaced with real numbers and merged without a first real run.

**Related, from the same PR:** pushing `compute_vars.py` to 837 lines (over
the 800-line god-module gate) was resolved by moving the new collector to
`scripts/analysis/_vars_zseries.py`, following the `_vars_registry` /
`_vars_retrieval` / `_vars_ablation` seam, and validated as a pure refactor
by `make -B` + `md5sum -c` byte-identity on the regenerated vars file — not
a green test suite. This is the standing "Refactor validation — byte-compare
the artifact" rule (rules/workflow.md), reapplied to a vars-file split.

Related: [[feedback_stale_by_construction_needs_cause_check]],
[[feedback_vars_file_provenance]],
[[feedback_worktree_make_check_corpus]].
