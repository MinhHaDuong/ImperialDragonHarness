---
name: repo-prepares-upstream-it-ships-nothing
description: "Author correction 2026-08-30 — this repo explores, designs, and prepares the upstream PR; never frame repo-side code as implementation, and design elements bundle into the prepared upstream contribution"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 27d49b3d-9f4e-42a2-aad0-03c30e4181b7
  modified: 2026-08-30T10:43:53.539Z
---

On ticket 0140 the session reported "PR ready" for repo-side work and framed
action 4 (the embed-call truncation guard) as a deferred standalone upstream
filing for the author to authorize someday. The author corrected both: "That's
not the spirit. Here is only to explore and design and prepare PR FOR
UPSTREAM. So the truncation true should bundle."

**Why:** the deliverable of this repository is the upstream contribution to
oscardvs/zoteus — documents, tickets, measurements that *prepare* it. bench/
code is harness, not product. A design element left as "an author decision
about a possible separate filing" is the drift: it belongs designed into the
upstream PR being prepared (here: the guard rides inside seg/1's PR, ticket
0028, the change that creates the exposure). Ruled in spec/DECISIONS.md
2026-08-30.

**How to apply:** when a ticket action touches upstream code, the default
disposition is "bundle into the upstream PR this work prepares", recorded in
the ticket that prepares it — not "standalone filing awaiting authorization"
and not "skip". Frame repo PRs as spec/measurement records, never as the
implementation being done. See [[execute-authorized-outward-actions]] for the
complementary rule once the author authorizes an outward action.
