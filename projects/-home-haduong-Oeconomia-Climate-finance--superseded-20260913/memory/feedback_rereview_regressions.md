---
name: feedback_rereview_regressions
description: Review fixes can introduce regressions — re-review must verify both original fixes and new code
type: feedback
---

Review fixes can introduce new bugs. The dedup refactoring dropped a `log` assignment in `qa_detect_language.py` that would have crashed at runtime.

**Why:** Two independent re-review agents caught the same bug. Without re-review, a regression would have shipped.

**How to apply:** When review fixes touch multiple files (especially refactoring/extraction), the re-review must verify that all affected files still work, not just the primary target. Pay special attention to removed code — check if anything essential was accidentally swept away.
