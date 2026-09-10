---
name: feedback_ancestor_of_main_is_not_current_with_main
description: "merge-base --is-ancestor HEAD origin/main exits 0 both for 'your work is merged' and for 'this checkout is behind main' — passing roar's pre-check is no evidence the tree carries main's content"
metadata:
  type: feedback
---

`git merge-base --is-ancestor HEAD origin/main` is roar's pre-check for "the
branch has been merged". Exit 0 answers a containment question, and containment
has two causes that the exit code folds together:

- the branch's commits are now in `main` — merged, what the check means; and
- the branch is simply **behind** `main` and always was.

Both are "HEAD is an ancestor". So a green pre-check says nothing about whether
the working tree carries main's content, and every later step that greps "the
codebase" reads whatever that checkout happens to hold.

**Why:** on 2026-09-10, roar step 3 swept `scripts/guard-*.sh` minutes after PR
#869 deleted `block-pr-merge-in-worktree.sh` on `main`. The sweep found the file
present and reported on its contents. The primary checkout sat on an unrelated
feature branch that was an ancestor of `main` — pre-check green, tree stale by
several merges. The only thing that caught it was knowing the file should have
been gone; a sweep for something unfamiliar would have returned a confident
wrong answer, in either direction.

This is the resident family shape — a result whose "all clear" cannot be told
from "I could not look" — reached through a predicate that is doing exactly what
it was asked. Nothing is broken; the question is narrower than the use.

**How to apply:** sweep against the ref, not the checkout —
`git ls-tree -r --name-only origin/main -- <dir>` to enumerate and
`git show origin/main:<path>` to read, which is also the safe way to read
another version (never `git checkout <ref> -- <path>`, which writes the index).
Where the tree must be current, the discriminating probe is the opposite
direction: `git merge-base --is-ancestor origin/main HEAD`, or
`git log --oneline HEAD..origin/main` being empty.

Related: [[feedback_erg_ready_reads_current_branch_tree]],
[[feedback_hook_rename_is_a_two_phase_deploy]].
