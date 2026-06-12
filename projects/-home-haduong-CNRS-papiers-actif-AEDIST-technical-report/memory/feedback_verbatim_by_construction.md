---
name: feedback-verbatim-by-construction
description: "For surgical edits to data files, prefer line filters (grep/sed/awk) over parse/serialize round-trips — verbatim by construction beats verbatim by verification"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e2c43e27-0ba8-4697-8789-f99a8209cd45
---

A 130-line python builder using `csv.DictReader/DictWriter` silently rewrote
an entire reference CSV from CRLF to LF (326-line diff for 2 logical edits);
its byte-fidelity had been "verified" only python-output-vs-python-output.
The 15-line grep/sed/awk replacement left untouched lines byte-identical by
construction, and the diff against the source showed exactly the intended
edits. The user's framing: "c'est pas un awk réinventé ?" — it was.

**Why:** parse/serialize round-trips normalize invisibly (line endings,
quoting, float formats); a clean diff-vs-source is the real provenance
evidence, and only construction guarantees it.

**How to apply:** when a change is line-shaped (delete/replace whole lines),
use text filters plus loud count guards (`test $(grep -c …) -eq N`); reserve
csv/json parsing for changes that are field-shaped. Always end by diffing
output against source and checking the diff is exactly the intended edits.
Related: [[project-reference-fix1]] (the builder this killed was itself
leapfrogged days later — don't gold-plate interim artifacts).
