---
name: feedback_gh_projects_classic_error
description: gh pr edit/merge emit a fatal-looking Projects-classic GraphQL error on this repo; use gh api REST and gh pr ready
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e941c29d-5c40-4794-8c38-de28cfeab946
  modified: 2026-07-27T14:11:51.943Z
---

On the climate-finance repo, `gh pr edit` and `gh pr merge` print
`GraphQL: Projects (classic) is being deprecated ... (repository.pullRequest.projectCards)`
and **exit non-zero even when the underlying action would succeed** — because gh
fetches deprecated Projects-classic data as part of the mutation.

**Why:** the repo still has Projects-classic associations; gh's GraphQL query for
them errors, aborting `gh pr edit` (title/body never applied) and making
`gh pr merge` look failed.

**How to apply:**
- To edit a PR title/body, bypass GraphQL with REST:
  `gh api -X PATCH repos/MinhHaDuong/climate-finance-het/pulls/<N> -f title='...' -F body=@<file>`
  (exit 0, no projectCards fetch). The repo moved to `climate-finance-het`; the
  old `Oeconomia-Climate-finance` remote still works via redirect.
- `gh pr merge <N> --merge` may print the error + exit 1 but still merge — re-run
  and it reports "already merged". Verify with `gh pr view <N> --json state`.
- Bootstrap/roar-sweep PRs are created as **draft**; the merge queue rejects
  drafts ("Pull Request is still a draft"). Run `gh pr ready <N>` first.
- **Never pass `--delete-branch` on this repo.** The repo already has
  `delete_branch_on_merge: true`, so the remote branch is deleted server-side
  and the flag is redundant. What it adds is a *client-side* `git checkout main`
  step that aborts from any worktree with
  `fatal: 'main' is already used by worktree at '<primary>'` — always true in
  this harness, since the primary checkout holds main and agents work in
  worktrees. The merge itself lands before the abort (2026-07-27, PR #1167:
  exit non-zero, `mergedAt` set, merge commit `0a271a5`). Merge with a bare
  `gh pr merge <N> --merge`, then verify state; never re-run on the assumption
  it failed.

Related: [[feedback_verify_agent_worktree]]
