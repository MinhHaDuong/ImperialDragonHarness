---
name: verify deferral tracker on close
description: When a ticket defers an action to another ticket, check the tracker is still open before closing. Rehome if it has closed without covering the deferral.
type: feedback
originSessionId: 4253dea7-79a3-4c89-9916-fe2c79cbecc1
---
When closing a ticket that deferred work to another tracker (pattern: "tracked in NNNN", "deferred to NNNN"), verify that tracker is still `Status: open` and still scoped to cover the deferral. If the tracker has since closed — especially if it closed for a different reason (e.g., scope shifted, target document changed) — the deferred work is orphaned and needs a new ticket.

**Why:** Ticket 0086 deferred a technical-report methods paragraph to ticket 0034 (structural-breaks rewrite). 0034 was later closed on 2026-04-15 because its target shifted from the technical report to the companion paper — which had nothing to do with the deferred paragraph. The deferral went silently orphaned until discovered in an unrelated session (2026-04-21) and rehomed as ticket 0089.

**How to apply:** At `/celebrate` or `/ticket-close` time, grep the closing ticket's log/body for `tracked in|deferred to|tracker|parked under` + 4-digit IDs. For each referenced ticket: (1) read its current status, (2) if closed, read its close log — did its scope change? If yes, open a successor ticket with the narrowed deferral before closing the current one. Don't rely on future discovery.
