---
name: feedback-async-agent-continuation
description: "No SendMessage in this env — an async agent that \"completes\" with an escalation may still continue by itself; never relaunch a fresh finalize agent without isolation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: dd5fd1a6-54f6-4a9c-8dac-81a5fb68b497
---

When an async Agent completes with an escalation question, do NOT immediately launch a fresh "continuation" agent: (1) this environment has no SendMessage tool, but the original agent may still resume and finish on its own (the 0413 worker delivered PR #767 after its "escalation" completion notification); (2) a fresh agent launched WITHOUT `isolation: "worktree"` runs in the session worktree and will `git switch` it under your feet.

**Why:** 2026-06-05: relaunched finalize-0413 twice — first one switched the session checkout to the ticket branch (killed in time, read-only), then the ORIGINAL worker completed the job itself, forcing a second kill to avoid duplicate force-pushes to the same branch.

**How to apply:** after an escalation-shaped completion, answer the question to the USER first, wait one beat for the original agent's possible self-resume (check `gh pr list`/branch pushes for its fingerprints), and if a new agent is genuinely needed, always give it `isolation: "worktree"` and make it operate on the pushed branch, not the original worktree.
