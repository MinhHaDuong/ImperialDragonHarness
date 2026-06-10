---
name: feedback-worktree-agent-env-leak
description: "isolation:worktree agent needing the primary repo's gitignored .env can leak file edits to the primary checkout"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96516ff3-e9dd-43d9-94cc-9744a7da7120
---

An `isolation:"worktree"` execute agent (raid 0515, 2026-06-10) leaked +98
lines of runner code (`experiments/sota/exp2_naive_arm.py`) and a ticket edit
into the PRIMARY checkout (on main), not its worktree. Root cause: the prompt
told it to use the main repo's gitignored `.env` via
`UV_ENV_FILE=/home/haduong/aedist-technical-report/.env`; pointing the agent at
the primary path drew its file operations there too. The CUT reverted the code
*in the agent's worktree* (merged main was clean) but the primary working tree
stayed dirty, and `git -C <primary> pull` would have conflicted on the
moved-to-closed/ ticket. Caught only because `/gaze` flagged primary-repo dirt.

**Why:** worktree isolation only protects against edits made *with worktree-rooted
paths*. A gitignored resource (`.env`, API keys) exists only in the primary
checkout, so handing the agent the primary absolute path invites it to operate
against the primary tree.

**How to apply:** when an `isolation:worktree` agent needs a gitignored
secret/resource, copy it INTO the agent's worktree first (or pass the key via a
plain env var in the Bash command), so the agent never references a primary-repo
absolute path. After such an agent returns, `git -C <primary> status` to check
for leaked working-tree changes; clean with `git -C <primary> checkout -- <files>`
(never `cd` — the guard blocks it). Related: [[feedback_bash_cd_primary_repo_trap]],
[[feedback_killed_agent_salvage]].
