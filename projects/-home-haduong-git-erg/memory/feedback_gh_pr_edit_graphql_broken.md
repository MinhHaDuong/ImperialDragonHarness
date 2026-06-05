---
name: gh-pr-edit-graphql-broken
description: gh pr edit / gh pr view fail with GraphQL projectCards deprecation error; use gh api REST PATCH for PR body edits
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9767083e-ae2e-48c0-bb47-2750ac1f5dc7
---

`gh pr edit <N> --body-file ...` (and sometimes `gh pr view` in the same
pipeline) exits 1 with `GraphQL: Projects (classic) is being deprecated ...
(repository.pullRequest.projectCards)` on this gh version (observed
2026-06-04, raid 219-224).

**Why:** the GraphQL mutation path queries the deprecated projectCards
field; the failure is environmental, not request-specific. Retrying the
same command does not help.

**How to apply:** edit PR bodies via REST instead:
`gh api repos/<owner>/<repo>/pulls/<N> --method PATCH -f body="$(cat file)"`.
Plain `gh pr view --json body --jq .body` works on retry (stderr noise,
output intact) — capture with `2>/dev/null`.
