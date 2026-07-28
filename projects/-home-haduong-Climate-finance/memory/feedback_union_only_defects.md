---
name: feedback_union_only_defects
description: "A guard one PR adds can be violated by a sibling PR's addition — each branch green alone, the union red; only a composed-tree test run finds it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1a2a449-f55d-4143-847e-e015213fee2a
  modified: 2026-07-27T18:12:03.705Z
---

When two PRs land in the same wave and one of them adds a **mechanical guard**,
run the guard against the *composed* tree before merging the second. The sibling
may add exactly the pattern the new guard forbids. Each branch passes its own
`make lint`; only the union fails.

Concrete case (raid 0327/0329, 2026-07-27): 0327 added
`test_grouped_recipes_name_their_output_explicitly`, forbidding a bare `$@` in a
grouped Make target. 0329 independently added a `tab_retrieval_protocol` grouped
target using a bare `$@`. Both branches green; the merge would have broken
`make lint` on main. No conflict marker flags this — the Makefile text-merges
cleanly. The fix rides whichever PR lands second.

**Why:** a guard's blast radius is the whole repo, but CI (here: nothing, this
repo has no CI — see [[feedback_no_ci_local_merge_gate]]) only ever evaluates it
against one branch at a time. Grep-verifying the union catches dropped *content*
([[feedback_merge_conflict_all_hunks]]); it does not catch a *rule* newly
violated by content that was always there.

**How to apply:** in a multi-PR wave, ask "does any PR add a test that scans the
whole repo?" If yes, build the composed tree (`git merge --no-commit` in a
scratch worktree) and run that test before merging either. Same move when a PR
adds a lint rule, an adherence ratchet, or a schema.

Related: [[feedback_autodiscovery_class_guard]], [[feedback_regenerate_dont_merge_generated]].
