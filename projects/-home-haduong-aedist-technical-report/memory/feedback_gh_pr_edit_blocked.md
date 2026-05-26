---
name: gh-pr-edit-blocked
description: gh pr edit fails on this repo with classic-projects GraphQL deprecation error; use pr comment instead
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7e5c93fc-1bcf-4c10-af5d-1452e703ce1c
---

`gh pr edit <N> --title ...` and `gh pr edit <N> --body ...` both fail on this repository with:

> GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience, see: https://github.blog/changelog/2024-05-23-sunset-notice-projects-classic/. (repository.pullRequest.projectCards)

The PR is left untouched when the command fails. Do not retry — the failure is structural (GitHub API), not transient.

**Why:** Hit during PR #375 (ticket 0194 scope amendment, 2026-05-21). I needed to change the PR title and body after pushing an amended ticket; both edits failed. Used `gh pr comment` to flag the scope change instead.

**How to apply:** When you need to update a PR's title or body after creation, skip `gh pr edit` and add a `gh pr comment` flagging the change.

If the body absolutely must be correct (e.g. for `erg-pr-merge` which parses `**Ticket:** tickets/NNNN-...` from the body to find the ticket to auto-close), use `gh api PATCH` directly to bypass the `gh pr edit` projects-classic bug:

```bash
# Build the new body in a file (e.g. /tmp/pr_body.md), then:
jq -Rs '{body: .}' < /tmp/pr_body.md > /tmp/pr_body.json
gh api -X PATCH /repos/<owner>/<repo>/pulls/<N> --input /tmp/pr_body.json --jq '.body' | head -5
```

**Warning:** Do NOT use `gh api -f body=@-` to stream stdin — `gh api` does not read `@-` like curl does; it sends the literal string `"@-"` and clobbers the body. Use `--input <file>` with a `{"body": "..."}` JSON wrapper (`jq -Rs '{body: .}'` does the wrapping). Verified working PR #379, 2026-05-21.

Title edits via gh api PATCH are also possible (same endpoint, `{"title": "..."}` payload) if downstream automation parses the title.
