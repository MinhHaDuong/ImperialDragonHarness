---
name: stacked-pr-on-live-sibling-branch
description: "Stacking a PR on another session's in-flight branch — check ListAgents for the owner, message it, poll the PR state instead of waiting on a reply, and expect one tail collision per sibling merge in DECISIONS.md"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1b7498c5-45b0-4f3a-9888-a01f10e72b7e
  modified: 2026-09-02T07:38:45.049Z
---

A PR that amends text another open PR introduces has to stack on that PR's
branch. When that branch belongs to a live session (2026-09-02, PR 171 on
PR 169: a "gaze pr 169 reroll" session pushed two commits to it while my
review ran, one of them the same glossary dedupe I had made), the branch is
not mine to merge or rebase.

**Why:** merging or force-pushing a sibling's branch under a busy session
either races its reroll or destroys its unpushed fix. And the cross-session
message channel is not a wait primitive: the note was held for the user's
approval for several minutes, so a session that blocks on the reply idles
while the forge already has the answer.

**How to apply:**
- `ListAgents` before touching a branch with fresh commits you did not make;
  a session named for that PR is the owner.
- Message the owner with the facts (what conflicts, what stacks on it), then
  watch the PR's `state` with a background until-loop and continue on that.
- Merge the owner's tip into the stacked branch as often as it moves, so the
  stacked PR is already current when the forge retargets it to main.
- Every sibling PR that lands appends to `DECISIONS.md`, so the stacked PR
  re-conflicts once per merge, always at the awaiting-list boundary; the
  resolution is the union in landing order, asserted on the heading set of
  both parents (see [[append-only-merge-union]]). Three unions in one
  afternoon here, each mechanical.
