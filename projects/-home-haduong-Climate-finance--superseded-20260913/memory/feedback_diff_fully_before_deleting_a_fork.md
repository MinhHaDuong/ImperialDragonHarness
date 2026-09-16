---
name: feedback_diff_fully_before_deleting_a_fork
description: "Before deleting a duplicate document in favour of another, diff them section by section — the copy being deleted may hold unique content, and the survivor may be the wrong one"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 59128797-3c56-459e-9142-57f27d820f13
  modified: 2026-07-28T13:08:59.910Z
---

A project `.claude/skills/update-publist/` had drifted into a stale fork of the
harness skill of the same name, shadowing it. Deleting the fork was right, and
the three points of comparison used to justify it all held. Review then found
the comparison had been far too narrow: **six things existed only in the copy
being deleted** — a BibTeX entry-type table (including the rule that
`institution = {CIRED}` belongs to the working-paper series and nothing else),
a pre-upload PDF *content* review gate distinct from the survivor's *payload*
gate, a `halJournalId` lookup, the ORCID and HAL domain codes, a `-H "X-test: 1"`
dry-run step, and the `PUT` recipe for updating a deposit rather than
duplicating it.

Worse, the two documents disagreed on the CIRED HAL structure id, and resolving
it against the ref API showed the **fork was wrong and the survivor right** —
`struct-1002424` is ECOSYS, an unrelated laboratory. Deposits built from the
fork would have been filed under the wrong lab. Deleting it also erased the only
record that a disagreement existed, so nobody would have known to check.

**Why:** "which document is better overall" and "what does each hold uniquely"
are different questions. The first justifies the deletion; only the second tells
you what to carry across. Answering the first and acting is how a merge silently
loses content — and every point of *disagreement* is a latent factual error in
one copy, worth resolving against an external authority rather than by picking
the document you already decided to trust.

**How to apply:** when two copies of a document diverge, enumerate the sections
of each and diff the *union* before deleting either. Resolve every factual
disagreement against a third source — an API, the code, the filesystem — not by
preferring the copy you judged better. Port the unique content in the same wave
as the deletion, and record any disagreement you cannot resolve (here: whether
`~/CNRS/html` is a git repo, unverifiable because the tree does not exist on
padme) rather than letting the deletion settle it silently.

**2nd occurrence (2026-07-28, positive case):** a 0337 handoff branch was
superseded when the sibling agent reimplemented the removal ablation and merged
it (PR #1234). Before deleting the branch, the check was scoped to the *union
of deliverables*: the shipped `tab_filter_ablation.csv` was read and confirmed
to cover all five axes the ticket demanded (source/language/period/DOI/decile)
— only then was the branch deleted, with its recovery SHA recorded in the
conversation. The rule applied cheaply and nothing was lost.

Related: [[feedback_regenerate_dont_merge_generated]],
[[feedback_autodiscovery_class_guard]].
