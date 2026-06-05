---
name: erg verb drift in skill examples
description: The status verb was removed from %erg v1; skills with log examples drift toward it. Cross-check against spec-erg-v1.md when writing or reviewing.
type: feedback
originSessionId: c4344a78-dcaa-4704-9f19-d50e1fdccc12
---
When writing or reviewing %erg ticket log examples in skills or AGENTS.md, always cross-check against `tickets/spec-erg-v1.md`, not other skill files.

**Why:** The `status` verb was removed from %erg v1. Skills with log examples (found drifting in AGENTS.md for 0096, pick-ticket for 0098) reintroduce it because authors copy from other skill files rather than the spec. The spec is the canonical source.

**How to apply:** Correct verbs are `created`, `note`, `closed`. Any example log line using `status` is wrong and will fail `erg validate`.
