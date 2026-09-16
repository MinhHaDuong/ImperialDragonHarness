---
name: Verify agent must cd into PR worktree before running tests
description: Verify agents that don't cd into the PR's own worktree produce false REROLL results
type: feedback
originSessionId: b0ad69a4-551a-4c51-ad1d-3c2e0e738f34
---
When a verify agent runs `pytest` without first switching into the PR branch's worktree, it may test against a different code version and get false failures. Always `cd` into the PR worktree (or `gh pr checkout`) before running any test assertions.

**Why:** During 0119 verify, the agent ran tests in its own context rather than the PR worktree and got 2 false failures (S3 + S4 value mismatches). The fix agent confirmed the tests passed byte-for-byte in the actual PR worktree.

**How to apply:** In verify-gate agent prompts, always specify: "check out the PR branch or `cd` into the PR worktree before running tests." A passing test in the wrong directory proves nothing about the PR.
