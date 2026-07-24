---
name: PR scope discipline
description: Don't add architecture rules, tickets, or codebase-wide fixes to a feature PR — use a separate branch
type: feedback
originSessionId: 9625bcb9-58da-4ff8-9782-613290dca62c
---
Keep feature PR branches scoped to the feature. Architecture rules, new tickets, and codebase-wide sweeps belong on their own branch, even if discovered during review.

**Why:** PR #650 review session added arch rule 9 + tickets 0043/0044 directly to the feature branch. Had to revert them before merge. The owner force-pushed to remove the pollution.

**How to apply:** When a review uncovers a codebase-wide antipattern, note it for a follow-up branch. Don't commit it to the PR under review.
