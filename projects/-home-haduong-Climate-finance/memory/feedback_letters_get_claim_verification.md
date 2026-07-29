---
name: letters-get-claim-verification
description: "Correspondence to editors/referees gets an adversarial claim-verification pass before sign-off, same as manuscripts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 7916be61-b5ab-4c43-9ab3-33af97f51055
  modified: 2026-07-29T14:41:30.443Z
---

Before author sign-off, run every submission letter (cover, reply notes,
summaries) through an adversarial fact-checking pass: extract each checkable
claim (numbers, section/table pointers, artifact names, quote fidelity,
attribution of requests) and verify against the paper, the vars file, the
remark register, and the artifacts.

**Why:** RDJ-26561 revision 1 (2026-07-29): a 124-claim swarm on letters
already polished through ~25 interactive author rounds found 4 factual
errors — "no number is hand-typed" (probe statistics are typed literals),
"the replications you requested" (the editor requested none), and two wrong
section pointers. Interactive polish tunes tone and wording; it does not
re-check facts. The letter is the document the editor actually reads first.

**How to apply:** After the wording settles and before the DRAFT banner
drops, fan out verifiers over the correspondence exactly as over the
manuscript (the verify-reply-letters workflow pattern: extract per document,
verify in batches against ground truth, fix WRONG, leave UNVERIFIABLE
draft-state facts alone). Attribution claims ("you asked for X") deserve the
strictest check — misattributing a request to the editor grades them.
