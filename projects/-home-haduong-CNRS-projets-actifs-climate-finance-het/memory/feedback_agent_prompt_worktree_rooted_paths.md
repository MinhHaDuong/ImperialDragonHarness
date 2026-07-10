---
name: feedback_agent_prompt_worktree_rooted_paths
description: "A worktree-isolated Agent prompt must use worktree-rooted/relative paths, never the primary-checkout absolute path — else the agent edits the shared main checkout."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4ffdf7ae-8403-47bc-87ed-e116676de228
---

When launching an `Agent(isolation:"worktree")` coder, the prompt must NOT hardcode
the **primary-checkout absolute path** (e.g. `/home/haduong/CNRS/projets/actifs/climate-finance-het/Makefile`).
The agent takes those paths literally and edits the **shared main checkout on main**,
not its own worktree — the isolation guard is path-based, so an absolute primary
path sails straight through it ([[feedback_worktree_isolation_is_path_based]]).

**Why:** raid 0218 (2026-07-10). My execute prompt quoted the scoper's absolute
primary paths. The worktree-isolated agent edited the primary checkout's `Makefile`
+ `scripts/*.py`; its own worktree stayed clean (zero commits), and a parallel
session's `git checkout`/`reset` then wiped the leaked edits. Net: the whole
execute attempt landed nothing, and briefly dirtied a sibling session's checkout.

**How to apply:** In every Agent-coder prompt, tell it to `cd` into its worktree
first and reference files by **repo-relative path** (`Makefile`, `scripts/x.py`) or
by `$(git rev-parse --show-toplevel)/…`. When a scoping agent hands back
`file:line` refs rooted at the primary path, strip the prefix to relative before
pasting into the executor prompt. Same trap on the Bash surface (`sed -i /abs/primary/...`).
Related: [[feedback_enterworktree_stuck_cwd]], the harness "Worktree paths" rule.
