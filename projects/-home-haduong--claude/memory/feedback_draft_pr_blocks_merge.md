---
name: feedback_draft_pr_blocks_merge
description: A draft PR blocks every merge path with cryptic errors; check isDraft first, `gh pr ready` before merging — and erg-pr-merge bounces on draft AFTER closing the ticket
metadata:
  type: feedback
---

A GitHub PR left in **draft** state cannot be merged, and each merge path fails
differently and unhelpfully:
- `gh pr merge --auto` → `GraphQL: Pull request is a draft (enablePullRequestAutoMerge)`
- `gh pr merge --merge` → `GraphQL: Pull Request is still a draft (mergePullRequest)`
- `erg-pr-merge` runs its ticket close+archive+push **first**, then bounces on
  the draft state — leaving the ticket closed and archived locally but the PR
  unmerged. This is the non-idempotency trap: re-running fails `close: no ticket
  found`, so finish with `gh pr merge --merge` directly after `gh pr ready`.

**Why:** other sessions open PRs as drafts; the state is invisible unless you
query `isDraft`, and the merge error names GraphQL, not the draft, so it reads
as a transient glitch worth retrying (it isn't).

**How to apply:** before merging any PR you did not open, check
`gh pr view <n> --json isDraft`. If draft, `gh pr ready <n>` first. If
erg-pr-merge already closed the ticket before bouncing, do NOT re-run it — mark
ready and `gh pr merge --merge` directly. Bit twice in the 2026-07-10 merge
session (#457, #432). Related: [[feedback_dont_pre_close_ticket_in_execution]],
[[feedback_erg_pr_merge_needs_close_claim]].
