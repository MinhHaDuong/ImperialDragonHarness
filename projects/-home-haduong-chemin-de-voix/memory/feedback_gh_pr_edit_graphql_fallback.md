---
name: gh pr edit fails with Projects-classic GraphQL error; use REST API
description: On the MinhHaDuong org, `gh pr edit` fails with "Projects (classic) is being deprecated" GraphQL error. Workaround: fall back to `gh api PATCH /repos/.../pulls/N`.
type: feedback
originSessionId: 61fa187f-e864-4faf-b109-32780d54dacc
---
`gh pr edit <N> --title ... --body ...` fails on this org's repos with:

```
GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience, see: https://github.blog/changelog/2024-05-23-sunset-notice-projects-classic/. (repository.pullRequest.projectCards)
```

This is a GitHub-side bug — `gh pr edit` queries `projectCards` even when not asked to. The PR remains unchanged after the failed call.

**Workaround:** write the payload to a JSON file and use `--input`:

```bash
python3 -c "import json, pathlib; pathlib.Path('/tmp/payload.json').write_text(json.dumps({'body': open('/tmp/body.md').read()}))"
gh api --method PATCH /repos/<owner>/<repo>/pulls/<N> --input /tmp/payload.json
```

Note: `-f body='...'` with multiline body strings breaks at backticks/newlines. The `--input /tmp/payload.json` approach is robust for any body content. Also: the repo must be `MinhHaDuong/Tracing-Kieu` not `MinhHaDuong/chemin-de-voix` (different on GitHub).

**Why:** PR #45 (2026-05-11) needed a title/body update post-creation to add the ticket reference. `gh pr edit` failed twice; `gh api PATCH` worked on the first try.

**How to apply:** When `gh pr edit` returns the Projects-classic GraphQL error on a Tracing-Kieu / MinhHaDuong repo, switch to `gh api PATCH /repos/.../pulls/N` immediately rather than retrying. Verify with `gh pr view N --json title,body`.
