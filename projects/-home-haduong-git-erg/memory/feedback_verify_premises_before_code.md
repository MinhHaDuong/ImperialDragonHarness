---
name: verify-premises-before-code
description: "Before implementing a ticket's fix, verify empirically that the stated premise is true — bugs get filed on wrong observations."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ab5e5447-d280-4bd4-b5f3-9b0f3f0d028e
---

Raid 188-193 caught two false premises before any code was written:

- **0188**: Premise "2026-05-30 is a writing date, not a version tag → 404 risk" was wrong. `git ls-remote --tags origin` showed the tag exists and is signed. Fix was a discovery pointer, not a URL change.
- **0191**: Premise "rule 11 is documented but not enforced" was wrong. `logLineRE` enforces structural format (timestamp + ≥2 tokens). The issue was misleading docs, not missing enforcement.

**Why:** Tickets are authored by humans observing behavior, not reading code. Observations can be incomplete.

**How to apply:** Before writing code for a ticket, run the failing case empirically. `git ls-remote --tags`, `go test`, `erg validate` — cheap checks that can save an entire implementation. Check premise first; ask advisor if uncertain.

See also: [[doc-writing-conventions]]
