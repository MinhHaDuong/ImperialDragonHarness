---
name: Shared utilities in util.py
description: User wants reusable helpers in util.py with comprehensive tests, not inline code
type: feedback
---

Put reusable helpers (parse_number, strip_diacritics, etc.) in `src/aedist/util.py`, not inline in the caller.

**Why:** User explicitly asked for shared utility pattern — these functions will be reused across modules. Comprehensive parametrized tests in `tests/test_util.py` are required since other code depends on them.

**How to apply:** When writing a helper that could serve more than one caller, put it in `util.py` with full test coverage in `test_util.py`. Don't inline domain-agnostic logic in domain-specific modules.
