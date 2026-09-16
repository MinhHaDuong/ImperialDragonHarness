---
name: Singleton test isolation
description: When testing module-level singletons, reset internal state not just the config variable
type: feedback
---

When a module creates a singleton at import time (e.g. `_cache = _DiskCache(CACHE_FILE)`), setting the module's config variable (`module.CACHE_FILE = ...`) doesn't affect the already-instantiated object. Reset the singleton's internal state directly (`cache._path`, `cache._data = None`).

**Why:** `enrich_dois.load_cache()` test was silently reading real data (1316 entries) instead of the empty test file — the `_DiskCache` singleton was instantiated with the original path at import time and ignored later changes to `CACHE_FILE`.

**How to apply:** Any test that redirects a module-level path variable should check whether a singleton was already instantiated from that path. If so, patch the singleton's internals and reset memoized state.
