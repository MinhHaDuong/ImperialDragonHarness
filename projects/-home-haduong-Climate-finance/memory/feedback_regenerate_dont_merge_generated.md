---
name: feedback_regenerate_dont_merge_generated
description: "Resolve a conflict in a generated artifact by regenerating — but first prove the regeneration reproduces the other side's data"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5dc4f34f-6be9-445c-ad64-4385a54f11f8
  modified: 2026-07-27T14:18:55.983Z
---

When a merge conflicts inside a *generated* file (codebook, vars, tables),
resolve the source, regenerate, and **verify the regeneration reproduces the
other branch's data-derived values before committing**.

**Why:** on 2026-07-27 `codebook.md` conflicted between this branch's
description edits and a parallel ticket's data fix (0347 repopulated
`keywords_provenance`, moving its missingness from 100.0% to 99.4%). Hand-
merging rows would have mixed prose from one side with stale measurements
from the other. Regenerating blindly was the subtler trap: if the local
`extended_works.csv` had predated 0347, a regeneration would have silently
reverted their data fix while looking like a clean merge and passing every
test — the generated file carries no marker of which corpus produced it.

**How to apply:** `git checkout origin/main -- <generated-file>` for a
known-good base, regenerate to a scratch path, and grep the one value the
other branch changed. If it reproduces, commit the regeneration; if it
reverts, the local input is stale — refresh it or hand-apply your change onto
their version. Same discipline as the union grep in
[[feedback_merge_conflict_all_hunks]]: a clean merge exit proves nothing about
content.
