---
name: branch-as-claim
description: No claimed tag — branch existence is the claim signal; encoding external state in tickets is rejected by design
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1609069c-2bd9-4aaa-b331-dff3fa87323f
---

Do not introduce a `claimed` tag or any tag that encodes external process state into ticket headers. The project uses branch existence as the claim signal (`erg ready` checks branches).

**Why:** Author decided 2026-05-12 that a `claimed` tag would go stale faster than branches. The spec now says "no pending or claimed tag by design, external state must not be encoded in ticket description."

**How to apply:** If IDH or agents need to know whether a ticket is being worked on, check for an existing branch — never propose a tag for it. Related: [[doc-writing-conventions]] (spec is authoritative on this).
