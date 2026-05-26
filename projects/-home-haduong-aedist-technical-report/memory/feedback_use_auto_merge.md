---
name: use-auto-merge
description: "When erg-pr-merge fails because CI is still running, enable auto-merge with gh pr merge --merge --auto instead of waiting"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d4615f2a-fb8c-4e3c-89c1-305817ddc336
---

When `/merge N` fails with "CI has failing/pending check(s)", immediately enable auto-merge:

```bash
gh pr merge N --merge --auto
```

Then confirm with `gh pr view N --json autoMergeRequest` and move on. Do not poll or retry erg-pr-merge — auto-merge handles the gate automatically once CI passes.

**Why:** Waiting for CI to finish and retrying manually is wasted blocking time. The repo has auto-merge enabled globally; use it.

**How to apply:** Any time erg-pr-merge exits non-zero due to CI checks, switch to `gh pr merge --merge --auto` as the next step. Ticket close (erg close) still happens via erg-pr-merge on subsequent merge confirmation if needed, or via the **Ticket:** line in the PR body on merge.
