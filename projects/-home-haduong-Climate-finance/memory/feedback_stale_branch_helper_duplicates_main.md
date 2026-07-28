---
name: feedback_stale_branch_helper_duplicates_main
description: "A long-lived branch's private helper often duplicates one main has since hardened; adopt main's and delete the copy, never re-inline"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e1a2a449-f55d-4143-847e-e015213fee2a
  modified: 2026-07-27T18:12:16.139Z
---

A branch that sat open while main moved will have grown helpers that main has
since added *and fixed*. On integration, adopt main's version and delete the
branch copy. Check which one carries bug history before choosing.

Concrete case (raid 0327, 2026-07-27): branch t0327 had added
`pipeline_loaders.load_latest_run_report` — `sorted(glob(...))[-1]`. Main had
meanwhile landed `pipeline_io.latest_run_report`, which prefers the stable
`<stage>.json` a DVC stage can declare and ranks only well-formed timestamps,
precisely so a fixture named `catalog_merge__test.json` cannot outrank every
real report (tickets 0346, 0349). The branch copy *was* the bug those tickets
fixed. The worktree also held a staged, uncommitted revert that re-inlined the
glob into both callers — worse than either.

**Why:** the branch author could not have known; the hardening landed after they
branched. The tell is a helper whose docstring explains a rule ("lexicographic
order is chronological order") that main's version explicitly refutes.

**How to apply:** when integrating a stale branch, grep main for the helper's
*behaviour*, not its name — they usually differ (`load_latest_run_report` vs
`latest_run_report`). If both exist, read main's docstring for ticket
references: a helper citing tickets is the survivor. Save any discarded staged
work as a patch first.

Related: [[feedback_lean_methods]], [[feedback_reimagine_catches_stale_deps]].
