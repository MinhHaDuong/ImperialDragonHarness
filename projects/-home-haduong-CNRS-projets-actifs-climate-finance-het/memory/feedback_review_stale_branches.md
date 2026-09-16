---
name: Review agents and stale branches
description: PR review pitfalls — stale branches show phantom diffs, worktree agents can hallucinate scope issues
type: feedback
---

When reviewing PRs from branches behind main, `gh pr view` metadata (+N/-M) can be misleading — the actual diff against current main may be much larger due to intervening merges. Always run `git diff main...origin/<branch>` to see the true scope.

**Why:** PR #276 showed +7/-4 in metadata but the real diff included teaching rewrites, `in_v1` deletion, and backward-compat paragraph removal — all from being branched before those features merged. PR #274 correctness agent hallucinated "massive out-of-scope changes" from worktree state confusion.

**How to apply:**
- For prose PRs on stale branches, rebase before reviewing to isolate intentional changes.
- Don't trust PR metadata for branch age — check `git log main..<branch>` to see what's missing.
- Review agent findings about scope should be verified against `gh pr diff` before posting.
