---
name: feedback_stage_by_path_in_shared_checkouts
description: git commit -am in the shared primary checkout steals whatever a parallel session left uncommitted; stage by explicit path
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7edca1b9-893f-4ea5-9284-d24817150788
  modified: 2026-09-02T15:47:00.745Z
---

`git commit -am` stages every modified tracked file, not the files you edited.
In `search-works-for-zotero` the primary checkout is shared by several
concurrent sessions, and one of them routinely has work sitting uncommitted in
it.

Cost, 2026-09-02: a two-file documentation PR (#196, moving the document map
into `AGENTS.md`) was committed with `-am` while a parallel session had its
ticket 0569 ratification draft uncommitted in the tree. The commit swept
`DECISIONS.md`, `SPEC.md` and that ticket into a docs change. The PR then
reported CONFLICTING against files it did not claim to touch, because the
other session had meanwhile landed the same ruling properly as PR #197. I
reported the PR as "moves the document map and nothing else" — wrong — and it
only surfaced because the author asked whether it had merged. Recovery: rebuild
the branch from `origin/main` with `git checkout <branch> -- <the two files>`,
force-push, merge.

**Why:** a conflict in a file your PR never meant to edit is the tell, and by
then you have already misreported the change. `git status --porcelain` before
committing shows the foreign modifications, but only if you look.

**How to apply:** in this repo, always `git add <path> ...` then `git commit`,
never `-a`. After staging, run `git status --porcelain` and confirm the staged
set (`M ` in column 1) is exactly what you edited; foreign work shows as ` M`
in column 2 and must stay there. Same check before `gh pr create` — the forge
prints an "N uncommitted changes" warning that is other people's work, not
yours to resolve.

Related: [[feedback_preserve_agent_output]], [[feedback_stacked_pr_on_live_sibling_branch]].
