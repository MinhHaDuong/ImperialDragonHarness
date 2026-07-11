---
name: Orchestrator: serialize tickets, don't fan out
description: User runs MAIBA tickets one at a time, not in parallel — even when /orchestrator could wave them
type: feedback
originSessionId: 7b2e23f2-cad6-4682-b6d7-24bd090e73b4
---
When invoked with `/orchestrator <id>` for a single ticket, treat it as a serial step in a queue the user is driving by hand. Do not pre-empt or parallelize tickets that are also open.

**Why:** User explicitly redirected when I started executing a ticket while a sibling was still open: "I will do 10 after 9 not in parallel." They want to land each ticket cleanly through their own review before the next begins, not stack two unmerged PRs that touch overlapping surface.

**How to apply:**
- Before launching any execute agent for a ticket, check whether any sibling ticket touching the same surface is still `open` or `doing`. If so, stop and ask the user whether to proceed.
- The orchestrator skill's wave-management is fine for batches the user explicitly hands you ("/orchestrator all open" or a comma-list); it is NOT fine for "/orchestrator NNNN" where other tickets are mid-flight.
- Don't relitigate this — the user's queueing is intentional.
