---
name: feedback-raid-worktree-rebase
description: Raid execute agents run in isolated worktrees and miss same-session main commits — always rebase PR branch onto main before merging
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b5a6ca12-1650-436c-ad0a-e0d4f7ab8da1
---

Rebase the PR branch onto current `main` before merging when a raid execute agent built the branch in an isolated worktree. The worktree forks from a snapshot of main at creation time, so any commits made to main during the same session (ticket closures, migrations, etc.) will be absent from the PR branch — causing CI failures on validate-tickets or similar checks.

**Why:** Raid worktree isolation is correct for execution, but the merge step runs after the session has accumulated further main commits that CI expects to see.

**How to apply:** In Phase 7 (Merge), run `git fetch origin main && git rebase origin/main` on the PR branch before calling `erg-pr-merge`. Also watch for `erg migrate` side-effects: the `init` subcommand refreshes AGENTS.md/integration.md/spec from the binary's embedded templates, which may re-introduce legacy verbs that the status-verb-guard will catch.
