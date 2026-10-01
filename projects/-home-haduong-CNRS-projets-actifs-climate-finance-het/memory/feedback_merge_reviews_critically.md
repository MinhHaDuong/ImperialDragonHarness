---
name: feedback_merge_reviews_critically
description: "Merging many reviewers' findings is design by committee; admit a fix only if it serves a requirement, cut before adding, word budget, weigh arguments not votes"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 99c20e86-e272-4f1d-999a-588c6d03f2c1
  modified: 2026-09-30T20:42:36.754Z
---

When folding multi-reviewer findings (internal lenses, external models) into a specification, merge critically: a finding is applied only if its fix serves a named requirement or milestone; machinery without a product need is rejected with the reason recorded; nothing enters the M2/M3 slice unless a result needs it; a finding that reopens an author decision is rejected; contradictions are fixed by removing one side before adding a rule; the spec must not grow in net words (additions paid by deletions); agreement between models is weak evidence (shared training). Follow with a pure-deletion simplicity pass.

**Why:** 2026-09-30, JETP Observer spec: two review waves grew it from ~48k to ~83k words; the author: "Make sure you merge critically. Design by committee is tricky." The critical merge kept words flat; the simplicity pass cut 9.5 % with no rule lost. Wave-1 fixes applied as "a sentence without the record it needs" were the main source of wave-2 blockers.

**How to apply:** give the merge agent these rules verbatim and demand before/after `wc -w` and a rejected-findings list for the author to overrule. See [[feedback_author_is_not_the_checker]], [[feedback_external_brief_stale]].
