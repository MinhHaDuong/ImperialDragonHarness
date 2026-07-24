---
name: merge-skill-rejects-multi-ticket-prep-prs
description: "erg-pr-merge requires a single `Ticket: tickets/NNNN-...` reference; raid-prep PRs that touch multiple tickets without closing any must merge manually via `gh pr merge --squash --delete-branch`"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff1f28d7-df07-4e2e-8181-0eb5c4a6e448
---

The `/merge` skill (`erg-pr-merge`) exits non-zero on PRs with no
`Ticket: tickets/NNNN-...` line in body or title — its purpose is to auto-close
a linked ticket on merge. PRs that don't close any single ticket fail this check.

**Why**: Hit on PR #158 (raid prep, amended 0244+0250, created 0251+0252, no
single ticket closing). The skill prints
"erg-pr-merge: no ticket reference found in PR body or title". Adding a
placeholder `Ticket:` would falsely close that ticket, so the skill is the
wrong tool.

**How to apply**: For prep PRs (raid staging, multi-ticket housekeeping, doc
sweeps that don't close anything), bypass the skill and use:

```bash
gh pr merge <N> --squash --delete-branch
```

After this, `gh` will try a local `git checkout <base-branch>` post-merge —
that step fails inside a worktree if the base branch is checked out elsewhere
("'master' is already used by worktree at ..."). The remote merge has already
succeeded; the local error is cosmetic. Verify with
`gh pr view <N> --json state,mergeCommit`.

Distinct from [[merge-skill-needs-bold-ticket]] (which is about plain `Ticket:`
being silently skipped when the field IS present — different failure mode).
