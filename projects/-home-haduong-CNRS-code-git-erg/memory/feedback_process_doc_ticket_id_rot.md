---
name: process-doc-ticket-id-rot
description: Process docs with operational steps referencing ticket IDs by number rot when those tickets close
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de38e869-11c6-4e9c-8a3c-5ff2172cb760
---

Any operational step in a process doc that says `erg log <NNNN>` or similar will rot when that ticket closes. Two instances were caught in the 0201 raid (UX-PROCESS.md and SECURITY-PROCESS.md).

**Why:** Tickets close; process docs live indefinitely. Logging to a closed ticket is semantically wrong and may hard-fail.

**How to apply:** When writing process docs, do not embed ticket ID numbers in operational steps. The run output (e.g., the run-log section of a checklist doc) is the durable record — no breadcrumb needed. If a standing tracker is needed, use a label or a persistent open ticket, but verify it's open before wiring it up.
