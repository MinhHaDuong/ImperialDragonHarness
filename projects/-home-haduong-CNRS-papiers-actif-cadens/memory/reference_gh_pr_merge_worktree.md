---
name: gh pr merge worktree conflict workaround
description: When gh pr merge fails with "'main' is already used by worktree", use the REST API directly (gh api -X PUT) instead
type: reference
originSessionId: 35c8b6cf-a45d-4464-98ce-71e58d3245e1
---
`gh pr merge <N>` tries to update the local main branch as a side effect. In an Imperial Dragon worktree setup this fails because `main` is checked out in the primary worktree:

    fatal: 'main' is already used by worktree at '/home/haduong/CNRS/papiers/actif/<project>'

Server-side merge without touching local state:

    gh api -X PUT repos/MinhHaDuong/<repo>/pulls/<N>/merge \
      -f merge_method=merge \
      -f commit_title="Merge pull request #<N> from MinhHaDuong/<branch>" \
      -f commit_message="<description>"

Then delete the remote branch:

    gh api -X DELETE repos/MinhHaDuong/<repo>/git/refs/heads/<branch>

Use `merge_method=squash` or `merge_method=rebase` if the repo prefers those. This project (cadens) uses `merge` commits — visible in `git log --oneline` as "Merge pull request #N from …".
