---
name: Wait for review before merging
description: Merge a PR only after the review agents have returned their results
type: feedback
---

Wait for review results before merging a PR, even for "trivial" renames.

**Why:** Review exists to catch bugs before they land on main. Merging before reviewers return defeats the purpose. Low-risk is not zero-risk.

**How to apply:** After creating a PR and launching review, wait for all review agents to complete and report back. Then merge, provided findings are clean or non-blocking. This is a sequencing rule, not a merge prohibition: once the review is in and a standing authorization covers the merge (e.g. the [[merge-review-merge-cadence]] grant), merging without a fresh confirmation is the intended behavior.
