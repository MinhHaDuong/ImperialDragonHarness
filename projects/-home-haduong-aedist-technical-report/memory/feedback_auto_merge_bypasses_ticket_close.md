---
name: feedback-auto-merge-bypasses-ticket-close
description: gh pr merge --auto merges server-side and does NOT close the linked ticket; only /merge (erg-pr-merge) does
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0260a84d-76b1-4100-aa48-b690ff582478
---

`gh pr merge <N> --merge --auto` (and any GitHub-side merge) merges the PR but
does **not** archive/close the ticket named in the PR's `**Ticket:**` line. The
close runs client-side: it happens only when you merge through the `/merge`
skill or invoke `erg-pr-merge` directly. So a PR merged via plain `gh pr merge`
leaves its ticket OPEN on `origin/main`.

**Why:** 2026-06-09, ticket 0492 — PR #888 merged green via `--auto`, but
0492 stayed open. Required a separate follow-up chore PR (#889) that ran
`erg close 0492 "<reason>"` and committed the `Closed:` header to archive it.

**How to apply:** If you want the ticket closed on merge, use the `/merge`
skill (atomic close+merge from the PR head branch). If you must use
`gh pr merge --auto` (e.g. to clear a CI block per [[feedback_use_auto_merge]]),
remember to close the ticket yourself afterward via a chore branch:
`erg close <id> "<reason>"` → commit → PR → merge. See also
[[feedback_erg_pr_merge_partial_success]].
