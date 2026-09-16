---
name: Reimagine phase catches stale dependencies
description: Always reimagine tickets before execution — dependency graphs go stale fast
type: feedback
originSessionId: 4fce2fc5-8792-42cb-b9a6-0a6fe78418d1
---
The reimagine phase discovered 4 tickets already done but not closed, and 5 tickets with wrong blocked-by references. Without reimagining, we would have wasted execution cycles on completed work and blocked on phantom dependencies.

**Why:** Tickets are written at planning time but code lands asynchronously across sessions. Dependency graphs decay within days.

**How to apply:** In orchestrator, always run reimagine agents before execution — even for tickets that look "ready." Check git log for merged implementations, not just ticket status fields.
