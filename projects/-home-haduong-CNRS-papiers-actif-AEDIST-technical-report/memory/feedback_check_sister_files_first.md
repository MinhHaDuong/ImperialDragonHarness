---
name: When patching shared infrastructure, check sister files for the right pattern
description: Before writing new integration code, look for an existing sibling file that already solves the same problem and crib from it.
type: feedback
originSessionId: cdaa7a19-9651-4adf-ae9d-cf8d5e977b3b
---
When patching shared infrastructure (a router integration, an API call shape, an output-record schema), the project usually has a sibling file that already does it correctly. **Read the sibling first.** Even if your patch works, writing from scratch costs time AND introduces inconsistency between files.

**Why:** 2026-04-30 — `query_rag.py` already had the correct Ollama pattern (uses `query_ollama_native` with `num_ctx = min(ctx_window, 81920)`). I patched `query_direct.py` and `query_multiturn.py` from scratch, called `query_ollama_native` without first adding the import, and the ruff post-edit hook stripped the import — twice. Tests blew up at runtime in production. If I had cribbed the import + call shape from `query_rag.py` in one Edit, the import would have landed atomically and the rule "group import + usage in the same Edit" would have been satisfied automatically.

**How to apply:**
- Before writing integration code in `query_X.py`, `worker_X.py`, `evaluate_X.py`, or any shared-shape module, grep for the same call (`grep -rn 'query_ollama_native' src/`) and read the sibling that already calls it.
- Copy the import block + call site as a unit into the new file in a single Edit. Then adapt to local variable names.
- This is the same principle as "don't write a one-off when a helper exists" but applied to integration glue.
- Sister-file harvest also catches the case where the sibling has a subtle handling (special parameter, dry-run flag, error trap) that's not obvious from the function signature alone.
