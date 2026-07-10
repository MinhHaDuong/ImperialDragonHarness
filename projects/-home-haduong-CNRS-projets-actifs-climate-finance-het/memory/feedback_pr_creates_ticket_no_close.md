---
name: feedback_pr_creates_ticket_no_close
description: "A PR that FILES a new follow-up ticket must use Ticket-ref / Ticket none — never **Ticket:**, which closes it on merge"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a71c13b1-4a51-47a5-a757-8a3af332cb10
---

When a PR's purpose is to *create* a new follow-up/tracking ticket (e.g. a roar-sweep ticket), do NOT put `**Ticket:** tickets/NNNN-...` in the PR body. `erg-pr-merge` reads that line as a close claim and would close the brand-new ticket on merge — defeating the point. Use `Ticket-ref: tickets/NNNN-...` to reference it without closing, plus `Ticket: none` so the PR closes nothing.

**Why:** hit this on PR #842 (filing ticket 0164 from the Gide wrap-up) — the first draft used `**Ticket:** 0164`, which would have auto-closed the ticket it was creating.

**How to apply:** ticket-creating PR → `Ticket-ref:` (reference) + `Ticket: none` (close nothing). Reserve `**Ticket:**`/`Ticket:` for PRs that genuinely *complete* the named ticket. See generic rule in `~/.claude/rules/git.md`.
