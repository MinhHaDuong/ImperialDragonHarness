---
name: feedback_ticket_pr_fast_path
description: "Ticket-filing PRs merge immediately after erg check plus a collision scan — no draft, no verify loop"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-27T14:12:06.205Z
---

A PR whose diff is only `tickets/*.erg` files goes: commit → push → `gh pr
create` (**not** `--draft`) → `erg check` → ID-collision scan → `gh pr merge <N>
--merge`. One turn, no review request, no `/verify`, no `/gaze`.

**Why:** the author asked for ticket PRs to merge without friction
(2026-07-27). The ceremony bought nothing measurable. A `.erg` file is
mechanically validated by `erg check`, `main` is unprotected on this repo, there
are no required status checks, and no CI exists to wait for — so
`allow_auto_merge` is off *and* pointless: GitHub's auto-merge waits on an empty
requirement set. The friction was procedural, never a gate. Do not propose
enabling auto-merge as the fix.

**How to apply:**
- Open ticket PRs ready, not draft. The draft state only adds a `gh pr ready`
  round-trip.
- The one real risk is the optimistic-ID collision, so keep that check and drop
  the rest: `git fetch origin`, confirm the ID is absent from `origin/main`, and
  scan open PRs for the same `tickets/NNNN` path. The PR under test matches its
  own scan — that hit is not a collision.
- Use `Ticket-ref:` in the body, never `**Ticket:**` — a PR that *files* a
  ticket must not close it, and `erg-pr-merge` closes every `**Ticket:**` line
  unconditionally.
- Merge with a bare `gh pr merge <N> --merge`; see
  [[feedback_gh_projects_classic_error]] for why `--delete-branch` aborts from a
  worktree.
- Scope stays clean: no rules, sweeps, or code ride a ticket-filing PR
  ([[feedback_scope_discipline]]).

This is the fast path for ticket *filing*. Code PRs keep the full gate.
