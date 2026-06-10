---
name: ""
metadata: 
  node_type: memory
  originSessionId: dd0eb522-684f-4a2a-b01b-778dad661840
---

On host padme, `/etc/profile.d/dev-cache.sh` exports
`PYTEST_ADDOPTS="--cache-dir=/data/cache/pytest"`. `--cache-dir` is not a
valid pytest flag, so every bare `pytest` / `python3 -m pytest` invocation
aborts with `error: unrecognized arguments` (rtk also condenses this to a
misleading "No tests collected"). Discovered 2026-06-10 during ticket 0237.

**Why:** the cache relocation intent is right (keep caches on /data, see
[[data-disk-model-store]]) but the spelling must be `-o cache_dir=...`.
The bug is masked in IDH because `make check` runs no pytest (ticket 0238).

**How to apply:** until the padme repo fixes the file, prefix test runs with
`PYTEST_ADDOPTS="-o cache_dir=/data/cache/pytest"` (or `PYTEST_ADDOPTS=""`).
The permanent fix (edit `/etc/profile.d/dev-cache.sh`, needs sudo) belongs in
the padme repo — file/check a ticket there, not in IDH.
