---
name: feedback_review_all_comments
description: PR review must address all findings, not just blocking ones — user enforces runbook discipline
type: feedback
---

Fix all review comments regardless of severity, not just blocking ones.

**Why:** User pushed back when findings 4-10 were dismissed as "follow-ups." The review runbook says "Fix, addressing all comments regardless of their apparent severity." The user expects this to be followed literally.

**How to apply:** After a PR review, create a fix for every finding (comment or request-changes). Only ticket separately if the issue is pre-existing and untouched by the PR (escalation policy). Never batch dismiss non-blocking findings as "deferred."
