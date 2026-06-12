---
name: stale-line-numbers-across-waves
description: "Feasibility-pass line numbers go stale after each merged wave — later-wave executors must re-locate targets by label/grep, never absolute lines"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4424934b-b287-478a-a8ea-f6434d656ca3
---

In a multi-wave raid on sequential tickets (0561→0562→0563, 2026-06-12), the
feasibility verifiers annotated tickets with exact line numbers verified
against the pre-raid main. Those numbers were correct for Wave 1 but stale
for Wave 3 (the 0562 restructure shifted every annex block by hundreds of
lines).

**Why:** each merged wave rewrites the file the next wave edits; absolute
line hints are only valid against the commit they were measured on.

**How to apply:** record the measured-at commit alongside any line hints in
ticket annotations, and instruct later-wave execute agents explicitly to
re-locate every target by label/grep ("never trust the absolute line
hints") — one sentence in the launch prompt prevented any mis-edit in
Wave 3. Related: [[verbatim-by-construction]] — the Wave 3 executor's
label-keyed block reassembly with a line-multiset guard was the right
verification shape for pure-move edits.
