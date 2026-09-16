---
name: pr-no-ticket-line
description: "erg-pr-merge fails when PR body has no Ticket: line; skip to gh api merge directly"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 60ffdb7a-3472-4ce2-b965-eb2267d2e033
---

When a PR is follow-on work (no associated ticket to close), `erg-pr-merge` exits with
"no ticket reference found in PR body or title". Do not add a dummy `**Ticket:**` line —
just merge directly:

```bash
gh api repos/OWNER/REPO/pulls/NNN/merge -X PUT \
  -f merge_method=merge \
  -f commit_title="your title (#NNN)"
```

**Why:** `erg-pr-merge` is designed for the one-ticket-one-PR workflow. Bypass it for
admin/follow-on PRs where there is no ticket to close.

**How to apply:** If the PR body has no `**Ticket:** tickets/NNNN-...` line and was
intentionally written that way (not a mistake), skip `erg-pr-merge` and go straight to
`gh api .../merge`. Also check for `strict: true` branch protection — if branch is behind
main, rebase + force-push first, then wait for CI before merging.

See also: [[erg-pr-merge-partial-success]]
