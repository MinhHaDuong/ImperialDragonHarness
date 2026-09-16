---
name: Fuzzy-corpus repo enforces PR-based merges
description: Direct push to main is blocked; also force-push to feature branches requires explicit user approval
type: project
originSessionId: 1fc9c85f-fca5-498b-afdc-e23121463aec
---
The fuzzy-corpus repository (on the author's GitHub) has a harness rule that
blocks direct `git push origin main`. The user routes all merges through
GitHub PR flow (observed 2026-04-20 when I offered "push main directly" vs
"open a PR", and the user chose PR).

Force-pushes to feature branches are also gated and require explicit user
approval — even when the force-push is for a clean linear rebase of a
single-author worktree branch.

**Why:** PR flow preserves review trail and avoids history rewrites visible
to the remote. The user values the GitHub merge commit as the canonical
integration record.

**How to apply:** For any change in this repo, default to: commit → push
branch (regular push, no force) → `gh pr create` → user merges on GitHub.
If a rebase creates divergence between local and remote branch, prefer
pushing under a new branch name over force-pushing the existing one, unless
explicitly authorized.
