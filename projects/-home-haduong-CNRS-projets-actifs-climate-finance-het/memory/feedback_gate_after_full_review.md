---
name: feedback-gate-after-full-review
description: "Don't run verify-gate until the full review fan-out (esp. correctness/red-team) has returned — a premature APPROVED gets overturned"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: abeb176f-22ca-461f-bb52-7bdffd08f43b
---

2026-07-08, PR #876 (0182 null model). I launched `/gaze` (which fans out adherence + review-pr's correctness/red-team/scope/consistency/doc panel + simplify + gate) and then fired `/verify-gate` separately and early — it returned APPROVED before gaze's own review-pr panel had come back. Minutes later the correctness and red-team reviewers landed two blocking defects (anchor list not table-sourced → circularity re-entered; modularity affine to within-share → not an independent second statistic). I had already told the author "FORTIFIED" on the strength of the premature gate.

**Why:** The gate validates exit criteria against *posted* review comments. If the deep reviewers (correctness, red-team) haven't posted yet, the gate approves on partial evidence — an APPROVED that a later reviewer overturns. On analysis/statistics PRs the red-team and correctness seats are exactly the ones that catch the load-bearing defects, and they run longest.

**How to apply:** Let `/gaze` run its own full loop to its own gate; do not fire `/verify-gate` manually while the review fan-out is still in flight. Wait for every review agent (especially correctness/red-team) to return before treating any APPROVED as real, and before reporting a verdict to the author. See [[user-moa-moe-contract]] and [[feedback_settled_debates_to_brief]].

**Recurrence 2026-07-09, PR #939 (0195 provenance test).** `/gaze 939 … merge on Approval` fanned out built-in-review + adherence + a `/review-pr` correctness panel. The first two returned clean in ~90s; I merged on those. The `/review-pr` panel returned ~6 min later and caught a real defect: the z-score provenance needle was the bare string `"25"`, a substring of `"250 most-cited"`, so the assertion passed vacuously. Cost: a follow-up fix PR #942 to anchor the needles (`"z ≈ 25,"`). Lesson sharpened: the built-in review + adherence returning is NOT "the full fan-out" — the `/review-pr` correctness seat is the slowest AND the one that finds load-bearing test/logic defects. Under "merge on approval", block the merge until every gaze-spawned agent has returned, not just the fast ones.
