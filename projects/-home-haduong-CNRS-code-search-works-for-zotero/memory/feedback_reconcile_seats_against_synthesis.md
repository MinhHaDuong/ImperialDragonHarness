---
name: reconcile-seats-against-synthesis
description: "A review synthesizer can silently drop a seat's blocking finding; reconcile the seat list against the posted synthesis before acting on it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9970023e-fc7f-4ab4-80ee-07075e1dc25f
  modified: 2026-09-01T06:01:12.516Z
---

In PR #129's round 2 (2026-08-31), the first red-team pass filed a BLOCKING
finding (outgoing ISSUE-DRAFT files invisible to the governance guard). Its
report was superseded in the relay by a later red-team pass that never
examined that surface, so the synthesizer posted "no blocker" and the finding
would have been lost. It was recovered only because the orchestrator
cross-checked every seat report it had received against the posted synthesis.

**Why:** seat reports travel through a relay (notifications, SendMessage
re-sends), and the synthesizer works from what reached it, not from what was
produced. Two seats of the same kind disagreeing by omission looks like
resolution and is not.

**How to apply:** whoever holds the full set of seat reports — usually the
orchestrating session, since notifications roll up to it — diffs that set
against the synthesis before treating the synthesis as the verdict. A
blocking finding absent from the synthesis goes back into the loop
explicitly, with its provenance. Related: [[green-prs-red-union]] (another
place where per-unit green hides a union defect).
