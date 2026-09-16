---
name: feedback_gh_mergeability_unknown_stall
description: "GitHub mergeability can read UNKNOWN repo-wide for ~10 min under rapid sequential merges; erg-pr-merge gates on it — retry with 30s sleeps, and note the server-side merge endpoint checks conflicts itself"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d6d0d59-8438-4787-abcf-815081fd8fff
  modified: 2026-07-28T13:09:13.667Z
---

During a four-PR merge run (2026-07-28), every open PR in the repo reported
`mergeable=UNKNOWN` / `mergeable_state=unknown` for roughly ten minutes while
sibling sessions were landing merges to main in quick succession. Each merge
to main queues a recompute for every open PR, and GitHub's background job
lagged far beyond the usual seconds. `erg-pr-merge` refuses on UNKNOWN
("resolve conflicts or try again in a moment"), so the run stalled without
any real conflict existing.

**Why:** UNKNOWN is a computation-pending state, not a verdict. Polling GET
`repos/{owner}/{repo}/pulls/N` both reads and re-queues the job, but under a
merge burst the queue drains slowly; a single poll or a 1-minute wait can
falsely suggest a stuck PR.

**How to apply:** wrap `erg-pr-merge` in a small retry loop (3–4 attempts,
30 s apart) that only retries when the failure text says UNKNOWN — the second
attempt typically lands. If the stall outlives that, the server-side merge
endpoint (`gh pr merge --merge`) performs its own conflict check and can
succeed while the cached flag still reads UNKNOWN — observed when PR #1241
landed at the same minute its pre-flight reported UNKNOWN. Reserve that
bypass for PRs with no ticket-close claim (the fast path); close-claim PRs
should keep going through `erg-pr-merge` so the ticket close stays atomic.

Related: [[feedback_gh_projects_classic_error]],
[[feedback_check_open_prs_for_ticket]].
