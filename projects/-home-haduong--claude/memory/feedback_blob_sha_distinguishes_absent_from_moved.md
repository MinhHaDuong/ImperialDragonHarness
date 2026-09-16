---
name: feedback_blob_sha_distinguishes_absent_from_moved
description: "git status cannot tell a deletion from a move once rename detection stops biting — compare blob SHAs across the commit to prove content landed elsewhere"
metadata:
  type: feedback
---

`git status` and `git diff --name-status` report a relocated file as a deletion
plus an untracked addition whenever rename detection does not bite — across a
large enough reorganisation, or when the file also changed. **"Deleted" and
"moved" are then indistinguishable in the output**, and reporting the first is a
data-loss claim that may be false.

Settle it by content, not by name:

```bash
git ls-tree -r <commit>^ --format='%(objectname) %(path)' | grep '<old-dir>/'
git ls-tree -r <commit>   --format='%(objectname) %(path)' | grep '<new-dir>/'
```

Identical `objectname` on both sides is proof the bytes landed — same blob, not
merely same filename. Where the file legitimately changed (an index merged by
union, say), fall back to checking that its entries survived in the new copy.

**Why:** on 2026-09-16 a project-key consolidation showed 412 deletions in the
harness memory store. Filename comparison across 11 slug pairs cleared ten of
them; the eleventh, `Tracing-Kieu`, had no same-named counterpart anywhere and
was reported as five orphaned files — a genuine loss. A peer session re-checked
by blob SHA and showed all four non-index files were **byte-identical** inside
`chemin-de-voix`, absent before the commit and present after: a project rename
recorded as add + delete. The index was the fifth file and had been merged by
union. Nothing had been lost, and the loss report was the wrong half of a
question filename comparison cannot answer.

**How to apply:** before reporting any file as lost, deleted or orphaned, run
the blob-SHA comparison. It costs two commands and converts a guess into a
measurement. The general form is the one this harness keeps rediscovering —
a probe that cannot tell "absent" from "I looked in the wrong place" is not a
probe. Related: [[feedback_content_match_recovery_needs_diff_verification]],
[[feedback_positive_control_validates_the_detector_not_the_enumerator]].
