---
name: cut-prose
description: "Cut a document to a word or page budget by removing whole passages before condensing anything. Ranks the removable passages against the coverage ledger, cuts them entire, then condenses the survivors until the budget is met. Use for a manuscript trim, a reviewer-mandated length cut, or a slot-limited abstract."
disable-model-invocation: false
user-invocable: true
argument-hint: "<document-path> <word-or-page-budget>"
---

# Cutting prose to a budget

Was `rules/prose/cutting.md`, resident in every session until 2026-09-09; its
trigger is a task, not a file, so it is a skill (ticket 0572). The one-line
pointer in `rules/prose/_all.md` — injected on every prose edit — is what makes
it discoverable mid-cut.

The default failure mode is condensation-only: every passage shortened in
place, none questioned. **Remove whole before you condense.** It is cheaper
*and* it improves the document, where condensation merely compresses it.

## The pass, in order

1. **Remove whole first.** Re-read asking of each passage: is it weak,
   distracting, redundant with an external artifact (a deposited table, an
   appendix, the data package), or serving no reviewer remark and no core
   argument? Rank the removable passages and cut them entire. Check each
   removal against the coverage ledger: no reviewer remark and no load-bearing
   claim may lose its only support.
2. **Condense the remainder.** Only once the whole-removal pass is done,
   condense the ranked survivors until the budget is met — then stop. Do not
   over-cut; a budget met is a budget met.
3. **Displaced ≠ deleted.** Content with archival value is not thrown away — it
   moves to the data package or appendix as a file, with a one-line pointer
   left in the text.

## Why this order

On a real data-paper trim (2026-07-24) a condensation-only plan was rejected by
the author in favour of asking first "which weak or distracting parts can be
removed whole?" The whole-removal pass found 633 of a 1 240-word target in seven
passage cuts — the largest being analysis results smuggled into the introduction
of a *data* paper, already duplicated in deposited tables. Condensation then
only had to cover the remainder. Whole removal both hit the budget faster and
left a better paper.

A cut plan that opens with condensation is the tell this skill exists to
prevent: a cut plan starts with the whole-removal pass.
