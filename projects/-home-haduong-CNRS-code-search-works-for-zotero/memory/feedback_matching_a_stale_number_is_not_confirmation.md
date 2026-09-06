---
name: matching-a-stale-number-is-not-confirmation
description: A fresh measurement that agrees with a recorded figure confirms nothing when both ran the same reader; ground-truth one document by needle before trusting a ratio
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c237237f-abd3-4b9c-94b8-0f98e597a30a
  modified: 2026-09-06T16:40:15.706Z
---

On 2026-09-06 a pack-versus-flat word ratio came out at 0,87 over 4 762 PDFs and was nearly reported as "the pack drops 13 %", because DECISIONS.md already carried "0,91 and 0,99, the difference being the excluded flows." Both numbers came from the same reader (`sdt_read.block_text`), which did not descend into list items, so every bibliography read as empty. The true ratio is 1,00.

**Why:** agreement between two runs of one instrument measures the instrument's repeatability, not the quantity. The wrong figure had sat in the ledger since 2026-08-31 and was quoted in a ruling. What broke the spell was not statistics but a needle: the missing vocabulary was "journal", "press", "university", and grepping one block's JSON for "University Press" found it inside a list block the reader skipped.

**How to apply:** before reporting any ratio from a structural reader, take one document, pick a phrase you know is in the source, and find it in the reader's output. If it is absent, dump the raw block that carries it and read the schema. Do this before the aggregate, not after. Related: [[probe-needs-discriminating-control]], [[verify-the-load-bearing-claim]], [[one-liner-no-ticket]].
