---
name: Circuit breaker in shared module from the start
description: Place shared exception classes in pipeline_io.py immediately, not in the first script that needs them
type: feedback
---

When adding a new exception or constant that multiple scripts will need (like RateLimitExhausted), put it in the shared module (pipeline_io.py) from the start — not in the first script that uses it.

**Why:** #590 defined RateLimitExhausted in enrich_dois.py, then #598 had to refactor it to pipeline_io.py for the sweep. Two commits instead of one.

**How to apply:** When a fix reveals a codebase-wide pattern (not just a single-script bug), design the shared abstraction first, then apply it everywhere in one pass.
