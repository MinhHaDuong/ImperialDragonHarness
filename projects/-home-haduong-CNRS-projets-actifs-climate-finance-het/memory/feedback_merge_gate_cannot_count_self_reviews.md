---
name: feedback_merge_gate_cannot_count_self_reviews
description: "The 2-review merge gate never reaches 2 on an agent-authored PR — the forge refuses a formal review from the PR's own identity, so /review-pr posts a comment"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-28T08:33:58.825Z
---

The project merge gate on `gh pr merge` requires two reviews for
`review:standard`. An agent-authored PR can never satisfy it: the forge refuses a
formal `REQUEST_CHANGES`/`APPROVE` review from the identity that opened the PR, so
`/review-pr` falls back to posting a **comment**, which the counter does not
count. Round 2 leaves the gate still reading 1 of 2.

Seen on PR #1238 (2026-07-28). Both review cycles genuinely ran and both found
real defects; the gate stayed shut on a counter artifact.

**How to apply:** don't route around it — `erg-pr-merge` merges through the API
and never trips the local hook, which makes bypassing it a one-word decision, and
that is precisely why it should be the author's call. Report the state (cycles
run, findings fixed, gate reads 1 of 2) and let the author invoke `/merge`.

Two mechanics worth knowing when they do:

- **`erg-pr-merge` is not idempotent past its close step.** If a previous run
  already closed and archived the ticket and pushed that commit, the re-run aborts
  with "close-claimed ticket(s) NNNN are absent from tickets/ at the branch tip".
  The documented resolution is `ERG_PR_MERGE_ALLOW_MISSING_TICKET=1` — verify
  first that the ticket really is in `tickets/closed/` at the branch tip with its
  `Closed:` header, then re-run with the override.
- **A `Ticket-ref:` pointing into `tickets/closed/` is not recognised** as a
  close-claim line, so the script errors with "no close-claim in PR body". For a
  PR whose diff *is* the close, or a follow-up to an already-closed ticket,
  write `Ticket: none`.

**Why:** the gate encodes "no unreviewed merge", which is right. What it cannot
encode is "reviewed by an agent that also wrote the code", and the honest response
is a human decision rather than a quiet API path
(→ [[feedback_no_ci_local_merge_gate]], [[feedback_gh_projects_classic_error]]).
