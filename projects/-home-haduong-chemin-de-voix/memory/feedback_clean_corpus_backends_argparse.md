---
name: clean-corpus-backends-argparse-bug
description: "clean_corpus.py --backends nargs=\"+\" consumes glob patterns as extra backend URLs when passed via clean_two_gpu.sh; pass globs BEFORE --backends"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a35f7c24-d6a7-4938-99a5-8e7811affaeb
---

`clean_corpus.py --backends nargs="+"` greedily consumes ALL positional-looking args. When `clean_two_gpu.sh` passes extra args via `"$@"` after `--backends`:

```bash
uv run scripts/clean_corpus.py --backends http://8080 http://8081 "$@"
```

The glob patterns become extra backend URLs: `backends=['http://8080', 'http://8081', '/path/to/chunks/*.txt']`, `globs=[]`.

**Consequences:**
- Wrong scope: scans all voix-* dirs instead of specified globs
- httpx "Request URL missing http://" errors for chunks assigned to glob-URL worker
- Those chunks get `errors` verdict, NOT written to manifest, remain retriable

**Correct approach:** Use `python -u` + `PYTHONUNBUFFERED=1`, and pass globs BEFORE `--backends`:
```bash
uv run python -u scripts/clean_corpus.py 'glob1' 'glob2' --backends http://8080 http://8081
```

Or run `clean_corpus.py` directly (bypass `clean_two_gpu.sh`) for targeted subset sweeps.

**Why:** Discovered 2026-05-14 when trying to clean only Leonardo IT chunks. Two spurious sweeps of all 13922 files ran before the root cause was identified. Ticket 0138 filed.

**How to apply:** Never pass glob args to `clean_two_gpu.sh`. For targeted sweeps, call `uv run python -u scripts/clean_corpus.py GLOBS... --backends http://8080 http://8081` directly.
