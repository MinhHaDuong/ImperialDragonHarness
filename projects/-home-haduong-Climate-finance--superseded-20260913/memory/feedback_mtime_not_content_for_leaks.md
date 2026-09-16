---
name: feedback_mtime_not_content_for_leaks
description: "To prove a write no longer happens, compare mtimes — identical content hides an idempotent leak"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 82aac5fe-ddfd-4e93-afb5-d90fabf6f6cf
  modified: 2026-07-27T15:54:34.156Z
---

Checking that a fix stopped an unwanted write by comparing file *contents*
before and after is not evidence. If the leaking writer is idempotent, the
bytes are identical and the check passes while the write still happens.

Cost of getting this wrong (2026-07-27, ticket 0346): after fixing two test
modules that wrote run reports into the DVC-tracked corpus directory, I
snapshotted `ls` + `md5sum` of all 141 files, ran the suites, re-checked, and
declared the leak closed — 141 files, same hash. The mtimes then showed the
fixtures had been rewritten during that very run. The leaked writes were
byte-identical, so content equality masked them completely.

**Why:** content answers "did the data change?"; a leak is about "did anyone
touch this?". They are different questions and only the second one is being
asked.

**How to apply:** to prove a write no longer happens, capture
`stat -c '%Y %n'` for the target files, run the thing, diff the stat output.
For a directory, `find -newermt` also works. Reserve content hashing for
"did the value change?" — a genuinely different assertion.

The corollary bit twice in one session: a green suite and an unchanged
checksum both looked like proof and were not. Related: [[feedback_assert_on_written_artifact]]
(assert on the file a script writes, not the dict it builds) — same family,
one layer out.
