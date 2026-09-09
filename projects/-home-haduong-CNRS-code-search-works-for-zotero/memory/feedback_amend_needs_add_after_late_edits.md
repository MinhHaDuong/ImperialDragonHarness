---
name: feedback-amend-needs-add-after-late-edits
description: git commit --amend reuses the staged tree unless you re-stage — edits made after staging but before the amend silently stay uncommitted
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1fdebb29-23af-4c69-80a0-fcb348964f4f
  modified: 2026-09-04T07:35:12.594Z
---

`git commit --amend -m "..."` without `-a` and without a fresh `git add`
amends the MESSAGE onto whatever was already staged for the previous
commit — it does not pick up working-tree edits made after that staging,
even ones made in the same turn just before running the amend.

**Why:** during raid work on ticket 0638, several small wording fixes were
made to a ticket file (Edit tool calls) after the file had already been
`git add`ed once, then `git commit --amend` was run to give the commit a
proper message. The amend succeeded and looked complete (tests passed,
checks passed against the working tree), but those specific late edits
were never re-staged, so they sat as an uncommitted diff for several more
steps — caught only because a downstream reviewer's report flagged
unexpected uncommitted content in the shared worktree.

**How to apply:** after any Edit/Write following a `git add` but before a
`commit --amend`, either re-run `git add` on the touched paths or use
`git commit --amend -a` (careful: `-a` stages all modified tracked files,
not just the intended ones). Cheapest habit: run `git status --short`
immediately before the amend and confirm it's empty or contains only
intentionally-unstaged files.
