---
name: feedback-erg-premature-autoclosure
description: erg-pr-merge autoclosed ticket 0224 when PR fixed only some sub-tasks; partial completion is not tracked
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 15b3b196-58af-4fed-b721-f4c3ca0ca9b9
---

`erg-pr-merge` autoclosed ticket 0224 when PR #419 merged, even though the ticket had multiple sub-tasks and only one was done. The merge script reads the `**Ticket:**` line in the PR body and closes that ticket unconditionally — it has no awareness of whether all exit-criteria checkboxes are ticked.

**Why:** Ticket 0224 covered stage-1 dates, stage-6 MCP reading, and stage-7 consumer dates. PR #419 fixed only stage-7. The ticket was reopened manually, but this added friction.

**How to apply:** When a ticket has multiple independent sub-tasks that will land in separate PRs, either:
1. Split into child tickets (one per PR) before work starts, so each PR closes exactly one ticket, OR
2. Use a tracking note in the PR body ("Partial: closes stage-7 sub-task only; stage-1 remains open") and delay adding `**Ticket:**` until the final PR.

Option 1 is cleaner. [[feedback-ticket-log-placement]]
