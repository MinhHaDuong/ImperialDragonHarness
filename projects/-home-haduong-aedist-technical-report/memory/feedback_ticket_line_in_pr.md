---
name: feedback_ticket_line_in_pr
description: Only put **Ticket:** in PR body when that ticket will actually be closed by the merge
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e23002cf-aa34-4dee-beda-f2985d7f7231
---

Only include `**Ticket:** tickets/NNNN-...` in a PR body when the PR's merge should close that ticket. `erg-pr-merge` closes the referenced ticket unconditionally on merge.

**Why:** PR #462 referenced ticket 0250 (execution ticket, still open) for loose tracking. erg-pr-merge tried to close it, hit Blocked-by validation, and had to be bypassed with `gh api` direct merge.

**How to apply:** If a PR is administrative work (adopt, doc update, config) with no ticket to close, omit the Ticket: line entirely. If tracking is wanted, use a PR comment instead.

See also: [[erg_premature_autoclosure]]
