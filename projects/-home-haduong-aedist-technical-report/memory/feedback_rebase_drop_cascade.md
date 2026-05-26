---
name: rebase-drop-cascade
description: "When a wave of PRs each adds to the same cross-cutting set (e.g. VALID_ROUTES), rebasing onto sibling-merged main DROPS the PR's own addition. Re-apply after rebase."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc8db06a-aaf1-4fe0-a819-b5271e0d6403
---

**Pattern observed:** Wave 2 SOTA adapters (4 parallel PRs) each added one new entry to `VALID_ROUTES` in `tests/test_models.py`. The verify-gate auto-fixed the test in each PR at round 2. But when merging sequentially, each subsequent PR was rebased onto a main that had a sibling's route addition — and the rebase resolved by KEEPING main's version, DROPPING the current PR's addition. Result: every merge except the first required a "resurrection" agent to re-apply the route registration post-rebase.

**Why:** When two branches both add to the same hash-set / dict / list block in the same file, `git rebase` sees the conflict and the auto-resolver (or the human) often picks one side. The PR's own contribution to the set is the side that gets dropped because main "wins" in a rebase-of-PR-onto-main.

**How to apply:**
1. **Detect early:** During wave-level integration review (raid Phase 6.5), grep for cross-cutting sets that multiple PRs touch. Flag as "expect rebase-drop on these files".
2. **Resurrection prompt:** When relaunching a merge agent, explicitly instruct: "after rebase, grep for your specific entry in the cross-cutting set; if absent, re-add it; then commit, push, re-verify".
3. **Better:** Land a tiny "coordination PR" first that adds ALL expected entries from the wave to the cross-cutting set. Then each adapter PR is a pure addition with no set-mutation conflict. Worth it for waves of 4+ PRs touching same registry.

**Wave 2 cost:** 3 of 4 merges needed resurrection (+5 min each, +1 force-push, +1 CI re-run). Manageable but a known cost — not a surprise.
