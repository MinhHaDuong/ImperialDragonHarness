---
name: a-stale-artifact-reads-as-live
description: "An on-disk log with today's dates proved nothing — its writer had been retired two versions back; check what still writes a file before inferring from it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c237237f-abd3-4b9c-94b8-0f98e597a30a
  modified: 2026-09-06T22:08:51.322Z
---

On 2026-09-06 I filed a ticket claiming 3 853 unpacked PDFs were the sitter's own defect, on 12 611 `UnloadedDataException` entries in `sdt-sitter-errors.jsonl`. Every entry carried that day's date and the file's mtime was an hour old. The writer had been retired two sitter revisions earlier — the repo's own launch record said "no code path writes that file" — so it described a build nobody runs. The roar sweep caught it before anyone worked the ticket; the retraction is PR #416.

**Why:** freshness is not provenance. A file's dates and mtime tell you when bytes were written, never by what, and a retired writer's output is indistinguishable from a live one's. The tell I walked past: I grepped the source for the filename and found nothing writing it, then read that as "I searched the wrong place" instead of as the answer.

**How to apply:** before inferring from any on-disk artifact, grep the current tree for what writes it, and check the repo's own version records for a retirement note. If nothing writes it, the file is history, not evidence. Same shape as the positive-control rule: an artifact that cannot say which version produced it cannot support a claim about this one. Related: [[matching-a-stale-number-is-not-confirmation]], [[judgement-must-not-outlive-its-subject]], [[probe-needs-discriminating-control]].
