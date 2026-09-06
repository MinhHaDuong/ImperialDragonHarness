---
name: fork-cwd-and-worktree-guard
description: "Working inside fork/ (git-ignored checkout under the worktree) makes the shell cwd persist there, and the worktree-identity guard then blocks every bare git; name the tree with git -C, and keep repo commits and fork commits on separate branches."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b7159928-959f-4103-8860-e2c11cdefc7a
  modified: 2026-09-03T10:29:50.222Z
---

The fork checkout (`make upstream-checkout`) sits at `<worktree>/fork/`, a
separate git repository ignored by the outer one. A `cd fork && npx …` in one
Bash call leaves the session cwd inside it, and from then on the
worktree-identity guard refuses bare `git` (it resolves to fork/, not the
worktree), and `cd <worktree> && git …` is refused too because the guard reads
the cwd before the cd. Relative paths in scripts also break.

**Why:** two repositories nested one inside the other, both live in one
session (2026-09-02, seg/1 build: fork branch `t0028-seg1` pushed to the
author's fork, repo record on `t0028-seg1-record`).

**How to apply:** address each tree explicitly: `git -C <worktree> …` for the
repo, `git -C <worktree>/fork …` for the fork; run node/npm with a `cd
<worktree>/fork &&` prefix in the same call and expect the cwd to stay there;
reset it with a bare `cd <worktree>` call before repo-side scripts. Commit the
fork's work on its own branch and push to the author's fork (`origin` there);
the outer repo ignores `fork/` entirely, so nothing in it rides a repo PR.
See [[preserve-agent-output]] for why the push matters before the worktree
goes.

**The same guard also refuses ordinary staging, and the tell is that it names
rtk** — even a plain single-path `git add` inside the correct worktree. The
mechanism and the remedies live in
[[reference_git_in_a_worktree_session]]; the short form is `\git add tickets/`.
One tip specific to this situation: for a read that would otherwise want a
shell redirect, `git diff <ref> HEAD -- <path>` prints to stdout and needs
none.
