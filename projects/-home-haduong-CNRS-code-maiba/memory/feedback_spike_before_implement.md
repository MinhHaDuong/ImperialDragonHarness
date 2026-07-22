---
name: Spike unverified library APIs before drafting tests
description: When a ticket prescribes specific imports/functions from an external library, run a 10-line spike to verify the API exists in the installed version before writing the TDD red test.
type: feedback
originSessionId: bedc8f6c-19b5-4a8f-8ef3-63817b717c63
---
When a ticket names specific library APIs (`hishel.CacheClient`, `hishel.FileStorage`, etc.) — verify the API exists in the version you'll install before writing the TDD red test or the implementation.

**Why:** Ticket 0009 prescribed `hishel.CacheClient` + `FileStorage`, but hishel 1.2 had renamed these to `hishel.httpx.SyncCacheClient` + `hishel.SyncSqliteStorage`. The drafted test would have failed for the wrong reason (ImportError, not assertion failure), wasting a TDD red-loop iteration. A 10-line spike before the red test confirmed the real API and the respx ↔ hishel transport interaction.

**How to apply:** If the ticket prescribes external-library symbols you haven't used recently, before writing the failing test or the implementation, run `uv run python -c "import X; print(dir(X))"` or write a 10-line spike that exercises the integration point. Update the ticket body with the corrected API reference and commit before launching the execute agent. Spike outcomes belong in the ticket, not in commit messages — future re-readers should see them as part of the ticket's context.
