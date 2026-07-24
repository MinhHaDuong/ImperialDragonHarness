---
name: gh pr edit fails with Projects Classic
description: gh pr edit silently fails when repo has Projects Classic — use gh api PATCH instead
type: feedback
---

`gh pr edit --body` fails with a GraphQL error when the repo has Projects Classic enabled. The error message mentions "Projects (classic) is being deprecated" but the edit silently does not apply.

**Why:** GitHub's GraphQL mutation for PR edits touches the projectCards field, which breaks on repos with legacy Projects Classic.

**How to apply:** When updating PR body/title, use the REST API instead:
```bash
gh api repos/{owner}/{repo}/pulls/{number} -X PATCH -f body="..."
```
