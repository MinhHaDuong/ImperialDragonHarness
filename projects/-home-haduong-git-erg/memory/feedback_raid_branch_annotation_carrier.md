---
name: raid-branch-annotation-carrier
description: Raid pattern — push the raid branch with annotated tickets; execute agents import via git fetch + checkout FETCH_HEAD -- tickets/X.erg
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9767083e-ae2e-48c0-bb47-2750ac1f5dc7
---

Raid imagine/plan annotations live on the raid session branch, which
fresh execute-agent worktrees (based on origin/main) cannot see. Solved
in raid 219-224 (2026-06-04), 5/5 clean:

1. Raid session commits annotated tickets per phase and pushes its
   branch (`git push -u origin <raid-branch>`).
2. Each execute agent's first steps: `git switch -c tNNNN`, then
   `git fetch origin <raid-branch> && git checkout FETCH_HEAD --
   tickets/NNNN-*.erg`, then commit the import.

**Why:** beats embedding full ticket bodies in agent prompts (token
cost, drift) and beats cross-worktree file reads (fragile). The PR
branch then carries the annotated ticket, so `erg-pr-merge` closes the
annotated version on merge.

**How to apply:** in any raid Phase 5 prompt, make the fetch+checkout
import steps 2-3 of the agent setup. Never leave annotated tickets
only on the raid branch — it never merges. See also
[[gh-pr-edit-graphql-broken]] for PR-body follow-up references.
