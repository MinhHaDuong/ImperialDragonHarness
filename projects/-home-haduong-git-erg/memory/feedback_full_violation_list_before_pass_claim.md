---
name: full-violation-list-before-pass-claim
description: "rtk-filtered output truncates erg check violation lists; get the full list (erg validate FILES, or redirect+count) before claiming PASS in a commit"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 28935cc7-f899-4c7d-abd7-a4079017615a
---

During the 0216 dogfood migration (cadens store), `erg check` output passed
through rtk filtering showed only the LAST violation of 14+; a commit was
made claiming "erg check: PASS" while 32 violations remained, caught only
because the next store surfaced one more.

**Why:** rtk compresses long tool output; a verdict read from the tail of a
filtered list is not a verdict. The commit message recorded a false claim.

**How to apply:** before asserting PASS in any commit/PR/report, obtain the
complete list: `erg validate tickets/*.erg tickets/closed/*.erg` (per-file,
complete), or redirect check output to a file and `grep -c VIOLATION`.
Never infer "one violation left" from one visible violation line. Related:
[[observation-before-causal-verdict]].
