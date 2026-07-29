---
name: feedback-pdftotext-grep-linebreaks
description: Never grep pdftotext output line-by-line for a phrase — line wraps split phrases and produce false negatives; join the text first
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d8f1ac34-d65e-4682-8b73-cc98690edfe6
  modified: 2026-07-29T16:45:52.372Z
---

A phrase probe against `pdftotext` output with plain `grep` returns a false
negative whenever the PDF's line wrap falls inside the phrase.

**Why:** on 2026-07-29 this produced a wrong provenance claim ("the release
PDF was built from the cut branch") that had to be retracted to the author:
the probe phrase was present but wrapped across two lines, so line-based grep
missed it, and absence was read as evidence.

**How to apply:** join the extraction before matching —
`tr -s ' \n' ' ' < out.txt | grep -c "phrase"` (or Python on the joined
string). Treat any single-phrase absence from an extracted PDF as unverified
until checked on joined text. Same trap class as [[feedback_rtk_log_hides_merge_commits]]:
a filter between you and the evidence makes "absent" indistinguishable from
"not visible through this filter".
