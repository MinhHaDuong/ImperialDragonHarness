---
name: project_proportionate_verify_pilot
description: "Since 2026-09-23 AGENTS.md § Verify replaces the /gaze full loop with checks chosen by what can break + one cross-model reviewer + /verify-gate; a pilot deciding /gaze's fate harness-wide"
metadata:
  node_type: memory
  type: project
  originSessionId: 927971ee-78e9-43c1-b08a-d1f151a487be
  modified: 2026-09-23T20:00:31.706Z
---

Opened 2026-09-23 (PR #1469). The rule lives in AGENTS.md § "Verify in
proportion to what can break"; aedist and maiba carry the same rule. The
author considered, and set aside, a path-routing script plus a Skill hook in
front of /gaze as adding machinery to fix machinery.

**Why:** /gaze's fixed overhead (fork, review worktree, fix agent, reviewer
scorecard) dominated its cost regardless of its size tiers; see
[[feedback_gate_proportionate_to_risk]].

**How to apply:** each PR states the checks it chose. After a week or two,
compare with the /gaze period: time open→merge, follow-up fix PRs after merge,
/lair step 9 failures, PRs missing the checks line. Then decide in the harness
whether to delete or shrink /gaze, reword git.md's "before /gaze" to "before
any gate", and retire raid Phase 6's per-ticket /gaze. Known /gaze bugs not
ticketed: `reviewers scorecard` retry loop, fix-agent budget too short for a
slow `make check`.
