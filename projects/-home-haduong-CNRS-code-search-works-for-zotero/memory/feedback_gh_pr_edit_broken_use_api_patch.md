---
name: feedback-gh-pr-edit-broken-use-api-patch
description: "gh pr edit --body-file fails on this repo's GraphQL Projects-classic deprecation and silently leaves the PR body unchanged despite a non-fatal-looking warning — use gh api -X PATCH instead"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b5a31a66-a51d-4a0e-833f-c09839038053
  modified: 2026-09-04T07:13:27.202Z
---

`gh pr edit <N> --body-file -` (or `--body`) on this repo fails with:

```
GraphQL: Projects (classic) is being deprecated in favor of the new Projects
experience... (repository.pullRequest.projectCards)
```

Exit code 1, but the error text reads like a secondary/non-fatal warning
about an unrelated deprecated feature — easy to misread as "mutation
succeeded, some other field just couldn't be queried back." It does not:
the body mutation itself fails, and the PR body is left completely
unchanged. The only way to catch this is to read the body back
(`gh pr view <N> --json body`) and check it actually changed — silence or a
non-zero exit alone don't prove the edit failed, and trusting the exit code
without verifying content is exactly the "check whose all-clear is
indistinguishable from could-not-look" trap.

**Confirmed independently twice** (2026-09-04): once by this session
directly on PR #326, once by a Fable execute agent on PR #341, unprompted —
both hit it and both worked around it the same way, suggesting the
workaround is standing knowledge worth keeping rather than a one-off retry.

**Workaround**: use the REST API directly, bypassing whatever GraphQL query
`gh pr edit` bundles the mutation with:

```bash
jq -n --rawfile body /path/to/body.md '{body: $body}' \
  | gh api repos/<owner>/<repo>/pulls/<N> -X PATCH --input - --jq '.number'
```

Do not use `gh api ... -f body=@file` — the `-f`/`--raw-field` flag's
`@filename` special-casing did not work as expected in testing (it passed
the literal string `@/path/to/file` as the body rather than reading the
file). The `jq -n --rawfile ... | gh api ... --input -` form above is the
one confirmed working.
