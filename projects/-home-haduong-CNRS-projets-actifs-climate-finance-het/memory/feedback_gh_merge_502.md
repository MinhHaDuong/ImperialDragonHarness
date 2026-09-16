---
name: GitHub merge 502 workaround
description: When gh pr merge hits GraphQL 502, use REST API PUT endpoint instead
type: feedback
---

When `gh pr merge` fails with a 502 Bad Gateway and then returns "Merge already in progress" on retry, the GraphQL endpoint is stuck. Use the REST API instead:

```bash
gh api repos/OWNER/REPO/pulls/N/merge -X PUT -f commit_title="..." -f merge_method="merge"
```

**Why:** GraphQL merge endpoint intermittently 502s on GitHub, leaving the merge in limbo. REST endpoint reliably completes.

**How to apply:** After a 502 from `gh pr merge`, switch to REST API merge immediately rather than retrying GraphQL.
