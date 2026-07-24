---
name: feedback-light-review-for-mechanical-diffs
description: User flagged energy cost of full raid+gaze armor on a mechanical search-and-replace diff — use the light review path for encoding/rename-class changes
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 56b08ff7-1e18-497f-aec3-a9f057ffe789
---

During raid 0558 (2026-06-12, em-dash `---`→`—` sweep, PR #1017) the user remarked: "That's lots of energy for a search and replace. My CO2 karma feels." The pipeline had spent a fable execute agent, two tectonic builds, two full `make check` runs, three parallel reviewers, and two gate rounds on a diff that was 214 instances of one three-character substitution.

**Why:** Review depth should scale with diff risk, not with the invocation path. A mechanical, self-verifying diff (pure substitution provable by transform-equality + identical pdftotext) doesn't need a three-reviewer panel.

**How to apply:** For single-ticket, mechanical-class changes (encoding sweeps, renames, path moves) prefer: direct execution or one fable agent, one `/code-review low` pass instead of the full gaze panel, and the gate. Reserve the full raid/gaze armor for behavior-touching or multi-ticket work. Related: [[feedback-subagent-model-effort-levers]].
