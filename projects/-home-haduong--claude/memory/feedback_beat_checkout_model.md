---
name: feedback_beat_checkout_model
description: "beat.py uses git checkout -B, not git worktree add — dirty main checkout carries into housekeeping branch"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 45233975-4845-46bc-ad71-9e512f6d40f9
---

beat.py switches branches with `git checkout -B branch base`, not `git worktree add`. Unstaged modifications in the main checkout carry over into the new branch, so a pre-flight dirty-tree check must run *before* the checkout to avoid wasting budget on a doomed run.

**Why:** `_raid` already had this pattern correct (pre-flight check at lines 1116-1122). `_housekeeping_phase` only had a post-skill check, so it burned ~$0.50 per blocked run before detecting the problem.

**How to apply:** When diagnosing beat dirty-tree aborts, check whether the main repo working directory has uncommitted changes — those are the root cause, not something housekeeping or the raid skill created. The fix is always a pre-flight check in beat, not "absorb the dirt" in the skill.
