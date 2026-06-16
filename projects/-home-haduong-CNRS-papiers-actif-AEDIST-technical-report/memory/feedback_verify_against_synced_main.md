---
name: feedback_verify_against_synced_main
description: Sync local main before any verification/review fan-out — a stale checkout yields false FAILs
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a0bed5cd-c7ef-4c4b-bb4c-87b251470dcd
---

Before spawning a verification or review team that reads the working tree, **sync the checkout to origin first** (`git fetch origin && git checkout main && git pull --ff-only`, or have agents read a freshly-fetched ref). Agents read files from the primary checkout's working tree — if local `main` is behind `origin/main`, they audit stale content and report fixes-already-merged as FAIL.

**Why:** 2026-06-14, the first 8-agent verification of ticket 0578's 42 findings ran against local main at `4ebe1a83` (pre-0591/0592). Findings 8 (Doc-07 codename) and 22 (code refs) came back FAIL — but those were already fixed in PR #1064/#1065, merged to origin and simply not pulled locally. The false FAILs had to be reconciled by reading the child tickets; a second red-team pass against synced main (`e5f782cc`) confirmed all clean. A whole multi-agent pass was partly wasted on a stale tree.

**How to apply:**
- `git fetch origin` + fast-forward local main (or branch) immediately before launching any read-only verification/review fan-out.
- When a verification FAIL contradicts a ticket/PR that claims the fix merged, suspect a stale checkout before suspecting a regression ([[feedback_rtk_git_log_stale]]).
- Background/parallel sessions especially: cwd and branch state are not yours (see Key insights — stale branch state).
