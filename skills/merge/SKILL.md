---
name: merge
description: Atomically close the linked ticket and squash-merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI).
user-invocable: true
argument-hint: [pr-number]
---

# Merge $ARGUMENTS

Run:
```bash
~/.claude/skills/merge/erg-pr-merge $ARGUMENTS
```

**Cross-repo prerequisite**: the caller must ensure cwd is the target
project and the PR branch is checked out before invoking `/merge`. For
cross-repo flows, this means `cd <project-path> && git fetch origin`
and checking out the PR branch before the call. The script itself is
cwd-based — it never takes a repo or path argument.

Report stdout/stderr verbatim. If the script exits non-zero, stop and show the error.
