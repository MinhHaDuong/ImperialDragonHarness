---
name: feedback_inspect_ref_readonly
description: To inspect another ref's content, use git grep/show — never git checkout, which mutates the working checkout
metadata:
  type: feedback
---

To read content at another ref (e.g. `origin/main`) for a sweep or comparison,
use read-only access: `git grep <pattern> <ref> -- <paths>`, `git show <ref>:<path>`,
or `git cat-file -e <ref>:<path>`. Never `git checkout <ref>` or
`git checkout <ref> -- <paths>`.

**Why:** `git checkout origin/main` detaches HEAD and rewrites the working tree.
In a primary checkout shared with parallel sessions, this silently knocks a
parallel session's branch off HEAD (2026-06-19 roar: detached the primary off
`t159-phase2-settings-path` mid-sweep; recovered with `git switch` only because
the tree happened to be clean — uncommitted parallel work would have blocked the
checkout or, worse, been at risk).

**How to apply:** during any roar/molt sweep that reads `origin/main` or another
branch, reach for `git grep <ref>` first. If you must materialize files, do it in
a throwaway `git worktree add`, not by checking out in place. See
[[project_repo_relocated_het.md]].
