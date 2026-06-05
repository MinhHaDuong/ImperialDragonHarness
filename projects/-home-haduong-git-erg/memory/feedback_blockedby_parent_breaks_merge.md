---
name: feedback_blockedby_parent_breaks_merge
description: "Never put Blocked-by:<parent> on a child ticket — it breaks erg-pr-merge's per-file validation"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 01c6929f-c6a6-45da-b152-420d1cf36c13
---

When splitting a tracking ticket into children (see ticket-new "Tracking ticket
convention"), link child→parent via the parent's **Children** body list + a
child log note — NOT a `Blocked-by: <parent>` header on the child.

**Why:** `Blocked-by` means "cannot proceed until that's done," but children
merge *before* the parent tracker closes — so the ref points the wrong way.
Worse, it breaks the merge: `erg-pr-merge` closes+archives the child, then
`git commit` runs the pre-commit hook, which validates the moved child file
**per-file** (`tickets/erg validate <file>`). In isolation the child's
`Blocked-by: <still-open-parent>` is unresolvable → "references unknown ticket
ID" → commit rejected → merge aborts mid-flight (ticket already closed+moved in
the working tree, PR not merged). `erg check` on the full corpus PASSES (it
sees the parent), which masks the problem until merge time.

**How to apply:** When creating child tickets in a raid/split, omit
`Blocked-by` pointing at the parent. If you already added it, remove the header
(keep the parent link in the log) before merging. Recovery from a half-merge:
`git restore --staged tickets/`, `git checkout HEAD -- <child>`, `rm` the stray
`tickets/closed/<child>`, then fix and re-merge.

Related: [[feedback_merge_script_skip]] (other erg-pr-merge failure modes),
[[reference_idh_tickets]].
