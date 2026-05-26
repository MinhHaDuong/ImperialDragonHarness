---
name: merge-skill-main-lock-wrinkle
description: "/merge exits non-zero when local 'git checkout main' fails because main is held by another worktree. GitHub-side merge already succeeded — verify, don't retry."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc8db06a-aaf1-4fe0-a819-b5271e0d6403
---

The `/merge` skill (and `gh pr merge`) attempts a post-merge local cleanup that includes `git checkout main` and `git branch -D <branch>`. When main is already checked out in another worktree (common during raids or housekeeping), `checkout main` fails with `'main' is already used by worktree at <path>` — the command exits non-zero either before or after the GitHub-side merge.

**Two failure modes:**
1. **Pre-merge failure** — `gh pr merge` never calls GitHub. Use `gh api repos/.../pulls/N/merge -X PUT -f merge_method=merge` to bypass the local git entirely.
2. **Post-merge failure** — GitHub-side merge already completed; the cleanup is cosmetic. Verify via `gh pr view`, never retry.

**Verify the merge succeeded:**
```bash
gh pr view <N> --json state,mergedAt,mergeCommit --jq '{state, mergedAt, mergeCommit: .mergeCommit.oid}'
```
If `state == "MERGED"` and `mergedAt` is non-null, the merge landed. Done.

**Do NOT retry** — retrying would conflict with the now-merged PR.

**How to apply:** Treat a non-zero exit from `/merge` (or `gh pr merge`) as ambiguous, not as failure. Always verify via `gh pr view` before deciding whether to act. Encountered repeatedly during Wave 2 SOTA raid (PRs #350/#351/#352/#353/#356/#357 — all hit this on the final cleanup step but all merged cleanly on GitHub).
