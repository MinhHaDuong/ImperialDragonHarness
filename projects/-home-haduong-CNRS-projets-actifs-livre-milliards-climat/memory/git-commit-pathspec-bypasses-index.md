---
name: git-commit-pathspec-bypasses-index
description: "git gotcha — `git commit -- <pathspec>` commits the working tree of those paths, silently dropping staged `git rm --cached` deletions."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e7796be7-c37c-43f6-8702-99dbdd355e78
---

`git commit -- <pathspec>` does a *partial commit* that reads the **working
tree** for the named paths, **bypassing the index**. So a staged
`git rm --cached <file>` (deletion in the index, file still present on disk) is
**silently ignored** — the file stays tracked, no error.

Seen 2026-06-17: untracking `docs/*` for the EDM workflow. `git rm --cached docs/*`
then `git commit -- docs/` produced a commit with **no deletions** (working tree
still had the files), leaving them tracked. Caught only by a post-commit
`git ls-files docs/`.

**Why:** pathspec-limited commit = working-tree snapshot of those paths, not the
staged index state. Untracking-while-keeping-on-disk lives only in the index.

**How to apply:** to commit an untracking, stage the removals and run a **plain
`git commit`** (no pathspec) — guard scope by ensuring nothing else is staged
first. Never trust a pathspec commit to carry `rm --cached`. Always verify with
`git ls-files <dir>` after. See [[edm-workflow]], [[verifier-dans-le-vrai-lieu]].
