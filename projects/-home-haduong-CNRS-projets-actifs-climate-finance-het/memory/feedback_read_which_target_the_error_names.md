---
name: feedback_read_which_target_the_error_names
description: A make/dvc failure tail often carries success lines directly above the error; read which target the ERROR names before attributing the cause
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 5d6d0d59-8438-4787-abcf-815081fd8fff
  modified: 2026-07-28T07:13:52.773Z
---

`make data` (= `dvc checkout`) exited 255 and I recorded the cause as "missing
`run_reports` cache blobs" in PR #1236's gate section. Both halves were wrong.
The output was:

```
A       data/catalogs/run_reports/          <- a SUCCESS line
ERROR: Checkout failed for following targets:
data/catalogs/catalog_merge_report.json     <- the actual subject
```

`run_reports` was the last thing to succeed, not the thing that failed, and the
real target failed for **absent hash info** (`dvc.yaml` declares two outs for
the `catalog_merge` stage, `dvc.lock` records one) rather than an absent blob.
Verified after the fact: all 133 `run_reports` member blobs were present in the
shared cache.

**Why:** a tail read for "what broke" latches onto the nearest recognizable
path, and in DVC/Make output the line immediately above an error is usually a
success. The wrong attribution then propagates — it reached a PR body, and
would have reached a ticket had the ticket not been written after re-running
the command.

**How to apply:** before naming a cause from a command tail, find the line that
*declares* the failure (`ERROR:`, `***`, `FAILED`) and read the target named on
or after it, not the nearest path above it. Then re-run the command to confirm
the symptom rather than quoting a remembered tail. Distinguish "blob missing
from cache" from "no hash info in the lock" — they look alike in the message
and have unrelated fixes. See [[feedback_check_the_detector_first]] for the
same discipline applied to a QA hit, and [[feedback_terse_reports]] on not
letting an unverified symptom into a report.
