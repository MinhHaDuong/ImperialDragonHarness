---
name: feedback_dead_recipe_check_makes_green_meaningless
description: "Before trusting a green browser recipe or check, verify the function holding the assertion is actually called; relay no agent's \"recipe passed\" without that"
metadata:
  node_type: memory
  type: feedback
  originSessionId: eae976b8-5082-4ce8-97e1-6c05a93a8951
  modified: 2026-09-29T16:15:40.130Z
---

A pass means nothing if the assertion never runs. Before reporting a recipe or check as green, grep that the function holding the relevant assertions is called from the entry point that ran.

**Why:** in the 0870 integration review (2026-09-29), padme's browser recipe `tests/browser/jetp_observatory.py` passed, and the ZAF and VNM recipe steps were reported green. `check_facts` (line ~496), which held SA3, VN3 and VN4, was never called by `check_site`. It also asserted a stale Bac Ai id and a typed count of 3. VN3 in fact failed: the served data had lost the sources the recipe expected, silently, at the 0878 retirement (hard-coded `source_links=[]`). I relayed the team-lead's "recipes passed" to the author before checking, and had to correct it.

**How to apply:** ask any team-lead reporting a recipe pass to name the function that asserted each recipe step. When dead check code is found, prefer deleting it and re-running the step by hand or by a scratch browser script over rewiring a stale function. See [[feedback_check_the_detector_first]], [[feedback_red_test_the_guard_you_wrote]].
