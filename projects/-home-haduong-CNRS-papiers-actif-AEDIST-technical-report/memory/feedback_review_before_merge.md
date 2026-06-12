---
name: Wait for review before merging
description: Never merge a PR before the review agents have returned their results
type: feedback
---

Always wait for review results before merging a PR, even for "trivial" renames.

**Why:** Review exists to catch bugs before they land on main. Merging before reviewers return defeats the purpose. Low-risk is not zero-risk.

**How to apply:** After creating a PR and launching review, wait for all review agents to complete and report back. Only then proceed to merge — and only if findings are clean or non-blocking.
