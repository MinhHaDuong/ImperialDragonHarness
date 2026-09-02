---
name: positive-control-before-waiting
description: "Before waiting hours on a silent long job, run a small instance of the same job as a positive control — a 250-page book reindexed in 30 s proved the 3-hour IPCC run was stuck, not slow."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b7159928-959f-4103-8860-e2c11cdefc7a
  modified: 2026-09-02T15:47:20.077Z
---

A long job that writes nothing until it ends (Zotero extraction writes the
cache only at the finish) gives the same picture whether it is working or
stuck: high CPU, no output. Three watches over three hours on the IPCC
reindex (2026-09-02) measured nothing; the first small reindex queued after a
restart answered in 30 s, and the IPCC volume then took 46 s.

**Why:** the time-based "wait until 17:00, then decide" plan had no
discriminator; a small instance of the same job is one, costs seconds, and
says which of the two readings holds. Same shape as the null-result rule in
`rules/workflow.md`: a zero is not a finding until a positive control fires.

**How to apply:** when a job is silent past its expected duration, do not
extend the watch; queue the smallest comparable job on the same path and
time it. If it completes, the big job is stuck — restart. If it also hangs,
the path is blocked. Order queues small-first so the control comes free.
Related: [[zotero-10-plugin-and-reindex]], [[probe-needs-discriminating-control]].
