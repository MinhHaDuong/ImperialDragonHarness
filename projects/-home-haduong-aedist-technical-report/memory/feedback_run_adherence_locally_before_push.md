---
name: run-adherence-locally-before-push
description: "Run `uv run ruff check .` and `pytest -m adherence` locally before every push — CI catches failures but the round-trip is wasteful."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 15b3b196-58af-4fed-b721-f4c3ca0ca9b9
---

Run ruff and the adherence tests locally **before every push**, not just when adding new files:

```bash
uv run ruff check .
uv run pytest -m adherence -q
```

**Why:** Burned CI cycles multiple times. PR #404/473 (color violations in plot files). PR #521 (PERF401 + invalid `# noqa` in stash-sourced code committed under time pressure to resolve git state). In all cases the fix was trivial and a local run would have caught it in 30 seconds.

**How to apply:** This applies to ALL commits, including code arriving via stash pop, cherry-pick, or merge conflict resolution — not just freshly written code. Stash-sourced code is especially risky because it was written in a different context and may not have been linted at write time.

Related: [[feedback_namespace_migration_trap]] (same theme — local tests catch silently-wrong state before CI does).
