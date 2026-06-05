---
name: feedback_no_ci_callback_wait
description: "Don't arm background waiters / Monitors to wait for GitHub CI — they don't work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 01c6929f-c6a6-45da-b152-420d1cf36c13
---

Do NOT set up a background Bash poll-loop or a Monitor to "call back" when
GitHub CI finishes. It does not work in practice: the waiters time out (cache
window), or complete *stale* after the PR already merged, generating
notification noise — and I end up polling `gh pr checks` by hand anyway.

**Why:** CI is external state the harness cannot track, so there is no reliable
auto-callback. Background loops over `gh pr checks` race against the merge that
follows and against their own timeout.

**How to apply:**
- To merge a PR, just run `erg-pr-merge` (`/merge`) — it already blocks on CI
  itself via `gh pr checks --watch --fail-fast` after the ticket-close commit.
  Don't pre-wait for CI before calling it beyond a single direct
  `gh pr checks <pr>` status check.
- When you genuinely need CI status, check it inline with one
  `gh pr checks <pr>` call at the moment you need it — do not arm a
  watcher/Monitor and "wait for the callback."

Related: [[feedback_merge_script_skip]], [[feedback_blockedby_parent_breaks_merge]].
