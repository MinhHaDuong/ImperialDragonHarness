---
name: control-arms-need-a-committed-tree
description: "Run control arms only from a committed tree — a helper that reverts with `git checkout --` destroys the uncommitted work it was meant to test"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7d53e650-daa2-4f6f-95ca-6fbf91967ae1
  modified: 2026-09-01T08:53:59.138Z
---

A control arm works by breaking the fix on purpose and watching the tests go red. The
natural helper is "edit, run, `git checkout -- src tests`" — and that last step reverts
**everything** uncommitted at those paths, not just the deliberate break. If the fix under
test is itself uncommitted, the control destroys it.

This cost two full redos in one session (2026-09-01, zoteus ticket 0091): a re-cut of a
fallback rule plus its tests, wiped by the helper's own restore, the second time after the
first had already been recovered by hand.

**Why:** the restore cannot distinguish the control's edit from the work the control exists
to validate — they are both just uncommitted changes at the same paths. `git checkout --`
is a write to the index and working tree that prints nothing, which is the same trap
`rules/git.md` records for reading a file at another ref.

**How to apply:** commit the fix *first*, then run controls, then restore with
`git checkout HEAD -- …` against a tree whose only uncommitted content is the deliberate
break. Amend afterwards if the controls change your mind. A control arm is a measurement of
committed work; if the work is not committed there is nothing to measure it against.

Related: [[feedback_the_tickets_own_test_needs_a_control]],
[[feedback_probe_needs_discriminating_control]].
