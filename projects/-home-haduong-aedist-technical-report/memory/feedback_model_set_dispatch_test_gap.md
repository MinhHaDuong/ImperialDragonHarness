---
name: --model-set dispatch path not covered by tests
description: Bug class where imports used only in if args.model_set: branch get stripped by ruff silently; all tests pass but runtime NameError guaranteed
type: feedback
originSessionId: 6d32ca44-1f31-4c87-a412-69801489b8e8
---
The `--model-set` dispatch path in all 6 query modules (`query.py`, `query_direct.py`, etc.) is never exercised by the test suite. Tests use `--models` (legacy path). This means:

1. Ruff sees symbols used only inside `if args.model_set:` as unused and strips them.
2. All 1144 tests pass. The bug surfaces as `NameError` at production runtime.

Caught in PR #326 verify phase — not by CI.

**Why:** The production path for `experiments.toml`-driven sweeps is `--model-set`. The test suite predates this path and was never updated to cover it.

**How to apply:** When adding new symbols to the `.harness` import block of any query module, verify they are used in BOTH the legacy path AND the `--model-set` path, or add a test that exercises `--model-set`. Ticket 0162 tracks the standing regression test.
