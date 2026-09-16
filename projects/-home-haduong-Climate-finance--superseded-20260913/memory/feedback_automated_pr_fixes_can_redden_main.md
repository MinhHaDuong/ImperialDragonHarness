---
name: feedback_automated_pr_fixes_can_redden_main
description: "Automated \"potential fix\" commits land on main unreviewed and can break it; check main is green after one appears on top of your work"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7073540a-d060-42dd-b562-d2bdb9e28a59
  modified: 2026-07-28T08:33:43.726Z
---

An automated review fix can land on main *on top of your merged PR* and break it,
with no one in the loop.

Seen 2026-07-28. Commit `d7d9789f` ("Potential fix for pull request finding")
was applied after PR #1233 merged. It restructured `products_named_in` in
`tests/test_datapaper_archive_layout.py` to handle a split extension
(`` `tab_retrieval_protocol.csv`/`.md` ``) — a genuine improvement — and dropped
the function's `return found` doing it. Every caller then received `None`. Main
was red until PR #1248 fixed it, and a parallel session and I both diagnosed it
independently.

The failure was doubly confusing because the guard's own blindness assertion
fired: three documents reported "names no deposit product at all", which is the
right alarm for the wrong reason — the extraction had not gone blind, the
function had stopped returning.

**How to apply:** when a bot commit appears on top of your work, read it and run
the affected tests before building on that base. If you merge main into a branch
and your *own* recently-landed code starts failing, suspect a post-merge
automated fix before suspecting your merge — check
`git log origin/main -- <file>` for a commit you did not write. Keep the
improvement and restore what it dropped rather than reverting wholesale (the
split-extension handling was worth keeping).

**Why:** the repo has no CI (→ [[feedback_no_ci_local_merge_gate]]), so nothing
runs the suite when such a commit lands. "It merged" carries no signal about main
being green, and that applies to automated commits most of all.
