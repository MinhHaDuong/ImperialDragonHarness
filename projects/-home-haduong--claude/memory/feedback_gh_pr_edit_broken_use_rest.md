---
name: feedback_gh_pr_edit_broken_use_rest
description: gh pr edit fails with a GraphQL Projects-classic deprecation error; edit PR bodies via REST gh api -X PATCH instead
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5a6bf32d-efe8-4cfc-a7d9-e82c60eb10aa
---

`gh pr edit <N> --body-file <f>` fails with `GraphQL: Projects (classic) is being deprecated ... (repository.pullRequest.projectCards)` — the gh CLI's edit path queries a sunset GraphQL field (observed 2026-06-03, gh on padme).

**Why:** the failure looks like a permissions/content problem but is an upstream CLI bug; retrying or rewording wastes time.

**How to apply:** use the REST endpoint directly:
`gh api repos/<owner>/<repo>/pulls/<N> -X PATCH -F body=@<file>` (or `-f body=...`). Other `gh pr` subcommands (view, merge, checks, close) are unaffected. Re-test `gh pr edit` after CLI upgrades and delete this memory when fixed.
