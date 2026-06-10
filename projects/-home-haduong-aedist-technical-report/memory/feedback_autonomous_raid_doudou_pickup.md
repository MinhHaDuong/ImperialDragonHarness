---
name: feedback-autonomous-raid-doudou-pickup
description: User wants everything merged for cross-machine pickup (doudou); autonomous mode = raid + roar + molt + end-session
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1ef5880f-4773-4ca8-a00f-f74fe0b97360
---

When user says "autonomous mode" with a destination machine (doudou, padme), run the full pipeline without pausing for confirmation: raid → roar → molt → end-session. Everything must be merged and pushed so the next session on the other machine starts clean.

**Why:** User has medical/commute and needs hands-free completion with clean handoff.

**How to apply:** Don't ask for confirmation between phases. Merge everything that passes review. Push all branches. Run cleanup skills at the end.
