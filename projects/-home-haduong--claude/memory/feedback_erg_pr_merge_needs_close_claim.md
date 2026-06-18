---
name: feedback_erg_pr_merge_needs_close_claim
description: erg-pr-merge exits 1 unless the PR body has a Ticket:/Ticket-ref:/Ticket: none line; put it in the body when opening, not at merge time
metadata:
  type: feedback
---

`erg-pr-merge` (the `/merge` skill) reads close intent from the PR **body only** and refuses to merge without one of: `**Ticket:** tickets/NNNN-...` (close claim), `Ticket-ref: tickets/NNNN-...` (cite without closing), or `Ticket: none` (closes nothing). Missing → exits 1 with "no close-claim in PR body" and merges nothing. Title prefixes like `chore(0216):` are never close claims.

**Why:** A skill-doc / config PR that closes no ticket still needs the explicit `Ticket: none` line — silence is an error, not a default. Bit on PR #398 (2026-06-18, a raid skill-prose edit): the body had only a description, so the first `/merge` bounced; adding `Ticket: none` and re-running merged it.

**How to apply:** Put the close-claim line in the PR body at open time, every PR — even doc/config ones. `gh pr edit` is broken here, so fix an existing body via REST (`gh api -X PATCH repos/.../pulls/N -f body=...`), see [[feedback_gh_pr_edit_broken_use_rest]]. Related merge-bounce behavior: [[feedback_erg_pr_merge_delete_branch_race]].
