---
name: reference_repo_no_ci
description: "climate-finance-het has no GitHub CI — erg-pr-merge's \"checks never registered\" abort is a false blocker; merge directly after mergeStateStatus CLEAN"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 6b29d291-f781-425c-a8bb-b18b28c2ab62
---

`climate-finance-het` (GitHub `MinhHaDuong/climate-finance-het`) has **no CI**:
no `.github/workflows/`, no branch protection on `main`, `delete_branch_on_merge = true`.
PRs therefore never register status checks (`statusCheckRollup` is `[]`; confirmed
on merged PRs #896, #897).

Consequence: `~/.claude/skills/merge/erg-pr-merge` aborts with
"CI checks never registered after 3 attempts" — a **false blocker** here, not a
real gate. When it fires, confirm the repo is genuinely CI-less
(`ls .github/workflows` empty + branch not protected + a prior merged PR shows 0
checks), then merge directly:

```bash
gh pr view <N> --json isDraft,mergeStateStatus   # want isDraft:false, CLEAN
gh pr merge <N> --merge --delete-branch
```

`--delete-branch`'s client-side checkout-to-main step errors in a worktree
(`'main' is already used by worktree at ...`) — harmless; the GitHub-side merge
and remote-branch deletion still succeed (deleteBranchOnMerge=true). Verify with
`gh pr view <N> --json state,mergeCommit`.

Draft PRs also block the merge queue ("Pull Request is still a draft") — run
`gh pr ready <N>` first. Quality gating here is `/gaze`, not CI.
Related: [[project_imperial_dragon.md]].
