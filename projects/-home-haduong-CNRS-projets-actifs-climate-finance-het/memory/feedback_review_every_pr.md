---
name: feedback_review_every_pr
description: Run /review-pr on every PR before declaring it ready — not just the first in a batch
type: feedback
---

Run `/review-pr` on every PR before declaring it ready, not just the first one in a batch.

**Why:** In the #527/#528 session, `/review-pr` caught stale doc references in #531 but #532 was never reviewed. A namespace violation (`handoff` instead of `corpus-handoff`) shipped unreviewed and was caught by the user.

**How to apply:** When opening multiple PRs in sequence, review each one independently before moving on. Don't assume that reviewing PR N covers PR N+1, even when they're related.
