---
name: feedback_concurrent_agent_can_merge_under_you
description: "Codex and this session both worked PR #298 concurrently; Codex merged it (under the shared forge account) while this session was mid-way into calling /verify-gate for a fresh recorded verdict — the fix had already landed, so the outcome was fine, but check ground truth (gh pr view) before assuming your own in-flight merge sequence is still the one that will happen."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c6fa2f07-2da2-48c6-801a-93ba027cd163
  modified: 2026-09-03T15:48:52.108Z
---

Recovered a crashed Codex session's work on ticket 0029 (search-works-for-zotero),
fixed a blocker a review found, force-pushed the fix, and was calling
`/verify-gate` for a fresh recorded merge-authority verdict when the user
interrupted: "Pause. Codex is merging I think." `gh pr view` showed the PR
already merged — by the shared `MinhHaDuong` forge account Codex commits
under — at a timestamp after this session's fix commit, so the merged
content was correct. But the merge itself skipped this session's planned
`/verify-gate` step and landed without a fresh recorded APPROVED verdict on
the page after the last fix (only a plain comment), which is a literal gap
against this repo's own merge-authority rule (`AGENTS.md` §Merge authority) —
harmless here only because the fix had already landed before the merge fired.

**Why:** two agents (a Claude session and Codex) can work the same PR at the
same time under the same forge identity, with neither aware of the other's
exact timing. A push-then-verify-then-merge sequence one agent plans can be
preempted by the other merging as soon as the branch looks mergeable,
regardless of which verification step is "supposed" to run first.

**How to apply:** when told another agent may be acting on the same
artifact, stop and check ground truth (`gh pr view --json state,mergedAt,mergeCommit`)
before continuing or re-verifying — don't assume your own in-flight plan is
still the operative one. If already merged, confirm the merged content is
what you expect (`git merge-base --is-ancestor <your-fix-commit> origin/main`)
rather than re-doing verification against a branch that no longer matters.
Report the actual state, not the state your plan assumed. See
[[feedback_reconcile_seats_against_synthesis]] for the general pattern of
distrusting a stale plan against live shared state.
