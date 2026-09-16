---
name: Fix failing tests in place, never hide them
description: Do not move, archive, or rename files to make failing tests disappear — fix the root cause instead
type: feedback
---

Never move, rename, archive, or delete files just to make failing tests pass. Fix the actual problem in place.

**Why:** Moving files out of sight is a common autonomous-agent antipattern — it "fixes" the test suite by removing the thing being tested rather than fixing the thing itself. This sweeps problems under the rug and loses work.

**How to apply:** When a test fails, diagnose why and fix the code or the test. If the test is genuinely obsolete, delete it explicitly with a commit message explaining why — but never relocate or hide files to dodge test failures.
