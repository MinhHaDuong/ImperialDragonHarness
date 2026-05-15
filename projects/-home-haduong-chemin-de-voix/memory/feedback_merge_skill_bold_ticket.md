---
name: merge skill requires **Ticket:** (bold markdown)
description: The /merge skill's auto-close looks for "**Ticket:**" with bold asterisks in the PR body. Plain "Ticket:" is silently skipped — the PR merges but the ticket stays open.
type: feedback
originSessionId: 61fa187f-e864-4faf-b109-32780d54dacc
---
When opening a PR whose merge should auto-close a `tickets/NNNN-*.erg` file, the body's ticket reference line must be:
1. **Bold markdown** — `**Ticket:**` (not plain `Ticket:`)
2. **Full path** — `tickets/NNNN-full-slug.erg` (not just `0072`)

```
**Ticket:** tickets/0089-clean-corpus-multi-backend.erg
```

Plain `Ticket:` (no asterisks) or a bare number (`**Ticket:** 0072`) is silently skipped — the PR merges, the ticket stays open.

**Why:** PR #45 used plain `Ticket:` (no close). PR #73 (2026-05-14) used `**Ticket:** 0072` (bare number) — merge script printed "no ticket reference found". Both required PR body edits before the merge script could run. Source: `erg-pr-merge` line 75 pattern `\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+`.

**How to apply:** Always write `**Ticket:** tickets/NNNN-full-slug.erg`. Copy the filename from `ls tickets/NNNN*`.
