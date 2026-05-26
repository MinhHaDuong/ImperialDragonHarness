---
name: feedback-verify-re-invocation-routes-healthcheck
description: "A second `/verify <pr>` invocation on the same PR (after a reroll fix) sometimes returns a healthcheck report instead of re-verifying. Fall back to invoking `/verify-gate` directly to get the round-2 verdict."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 05a0aece-0924-408e-95ce-e06061312fc0
---

The `/verify` skill behaves inconsistently on a second invocation against the same PR. Observed: after pushing a REROLL fix and calling `/verify 370` again, the skill returned a project-wide healthcheck instead of running phases 1–6 on the PR.

**Workaround:** invoke `/verify-gate <pr>` directly to get the round-2 verdict. The gate skill correctly assesses the fix against the round-1 blocker without re-running adherence/review-pr.

**Why:** Observed 2026-05-21 during the 0138/0139 raid. Caller had to manually fall back to `/verify-gate` to merge PR #370 cleanly.

**How to apply:**
- After a REROLL push, try `/verify <pr>` first; if it returns a healthcheck-style report, switch to `/verify-gate <pr>` rather than retrying `/verify`.
- The PR-state check (`gh pr view --json state,mergeable,statusCheckRollup`) confirms CI/mergeability cheaply before either skill call.
- Worth tracking as a `skill-doctor` candidate if the pattern recurs.
