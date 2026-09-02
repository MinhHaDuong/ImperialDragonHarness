---
name: takeover-handoff-pattern
description: "When a peer session takes over a ticket, the handoff that worked - explicit state check, durable record in the PR discussion, explicit ack, then hands off the lane completely"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9970023e-fc7f-4ab4-80ee-07075e1dc25f
  modified: 2026-09-01T06:01:29.461Z
---

On 2026-09-01, session "Ticke 91" took over ticket 0091 mid-flight at the
author's direction. The handoff worked first try. What made it work:

1. **State check on stand-down**: reply confirming no unseen/unpushed state,
   with exact SHAs (branch tips, fork branch), and naming what stays open
   (the disposition of the still-open PR, the unruled questions).
2. **Durable record, not transcripts**: the open points and review-gotcha
   histories were posted as ONE comment on the PR itself — session
   transcripts die, PR discussions persist — and the author explicitly asked
   for exactly this ("the reviews gotchas histories that should be in the PR
   discussion").
3. **Explicit ack requested**, because "the other session sees them" is a
   deliverable, not an assumption.
4. **Lane discipline after handoff**: no touching the ticket, the branches,
   or the PR's disposition; requests from the takeover session (e.g. run a
   review panel on its prepared branch) are honored read-only in ITS
   checkout, findings returned by message, never applied directly.

**Why:** the author runs parallel sessions; tickets migrate between them.
The failure modes are duplicated work, clobbered branches, and findings
stranded in a dead session's transcript.

**How to apply:** on any takeover message (either direction), do 1-4 above
before any other work. Related: [[preserve-agent-output]],
[[reconcile-seats-against-synthesis]].
