---
name: feedback_erg_spec_headers_immutable
description: New erg ticket headers are not permitted without explicit user approval; check spec-erg-v1.md before proposing additions
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 00214805-becd-45d2-b825-607057f60719
---

The erg ticket format headers (in `tickets/spec-erg-v1.md`) are a closed set. Adding new headers (e.g. `Blocks:`) is not permitted without explicit user sign-off.

**Why:** Adding a header also requires updating the erg binary to accept it; mismatched spec vs binary causes validation failures on all tickets that use the new header. PR #159 added `Blocks:` and had to be corrected by PR #164 because the user flagged it.

**How to apply:** Before designing a feature that requires a new erg header, ask the user first. If a feature can be implemented via inverse lookup of existing headers (e.g. `Blocked-by:`) or via prose conventions, prefer that. When reviewing SKILL.md or spec changes that introduce new header names, flag them for user approval before merging.
