---
name: feedback_raid_gaze_escalates_from_an_agent
description: Until ticket 0990 lands, a raid's Phase 6 /gaze launched as a background agent returns ESCALATE without reviewing; plan the review evidence the merge will rest on instead
metadata:
  type: feedback
---

Raid 0984/0987 (2026-09-29) launched Phase 6 exactly as `skills/raid/SKILL.md`
prescribes, one `/gaze` per PR as a background agent. Neither reviewed:

- PR #1061: the isolation guard blocked the review worktree (ticket 0853) and
  the panel had no Agent tool, so `PANEL-INTEGRITY: DEGRADED`.
- PR #1060: 16 files hit `/gaze`'s 15-file breaker; no earlier raid phase had
  counted the planned PR's files.

Both merged on author decisions, backed by `/hunt`'s three `/review-pr` rounds
plus, for #1060, one independent reviewer (a lower tier than the opus coder) on
the exact unreviewed commit range, trying to break each fix in a disposable
HOME. The waiver and its evidence went in a PR comment before the merge.

**How to apply:** at raid Phase 4, count the planned PR's files against the
breaker and propose a split while it is cheap. At Phase 6, expect the
escalation until 0990 is fixed: surface it to the author as a decision with the
evidence in hand, never as a stalled wave. Related: [[feedback_verify_fork_under_execution]].
