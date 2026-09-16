---
name: feedback_containment_guard_blind_to_second_file
description: "A `value in text` containment guard is satisfied by the first file carrying the current number; it cannot see a second file still quoting the stale one — assert the property (traces to the pipeline's current value) not a literal match, and search whitespace-collapsed text so a paragraph rewrap can't hide the line (0625)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f6a59d05-fc03-4ef4-8906-2e4ae1c5323b
  modified: 2026-07-28T18:06:07.859Z
---

Ticket 0625 (PR #1279, 2026-07-28) regenerated `tab_network_limitations.csv`
against the corpus `dvc.lock` now pins, and found the committed copy predated
it — nine numbers quoted verbatim in the RDJ26561 submission response were
stale, one (`boot_burden_rate`, "emerges in 8%") by more than half its own
value (8% -> 12.5%). Root cause matches ticket 0610's finding the same day:
a tracked Phase-2 artifact drifts from its producer whenever the corpus
`dvc.lock` moves, independent of any code change. Ticket 0641 now tracks a
systematic audit of every git-tracked Phase-2 artifact for this class.

**The existing guard passed throughout the stale period, and that is the
finding.** `test_response_letter_numbers_trace_to_artifact` asserted
`f"z = {z:.1f}" in md` — a plain containment check. It was satisfied because
one file (the memo) had already been fixed and the check ran against that
file; a second file in the same bundle (`response-letter.md`) still quoted
the old `z = 9.1` and nothing looked there. A containment check proves "the
current value appears *somewhere*", not "every file that should carry it
does" — the wrong property for a multi-file submission bundle.

**The replacement asserts the property, not the string.** The fixed guard
does two things a literal match cannot:
1. Discovers every `*.md` in the revision bundle (so a new response document
   is covered on arrival, not missed until someone remembers to add it to a
   file list) — except `external-review/`, explicitly skipped because it
   holds inbound referee text the guard must not "correct".
2. Matches a *class* of number (any degree-preserving z the pipeline
   generates) rather than one hardcoded value — round 2 of review found a
   second legitimate z (`lit_poles_z = 76`, a different analysis) that the
   first fix's "every z must equal this one" version would have red-lined
   the day it reached the response bundle. Widening the literal pattern would
   have re-created the same trap one spelling later; asserting "traces to
   *some* value the pipeline emits" does not.

**A paragraph rewrap defeats a line-anchored regex.** The three real z
occurrences sit at 63-73 characters in text wrapped near 77 columns — adding
one word upstream pushes the number to the next line and a per-line search
goes quiet with no other symptom. Fixed by searching whitespace-collapsed
text in a window around the anchor phrase, which no reflow can move the
number out of.

**Provenance pinning has the identical shape.** A second guard
(`test_response_provenance_names_the_pinned_corpus`) first searched the whole
file for the corpus hash — passed even after the document was split into two
"Corpus state" bullets (one per artifact, because the regenerated table and
the frozen spot-check now describe *different* corpora) if the hash sat in
either bullet. Same defect as the z-guard, one bullet over: presence anywhere
in scope, not presence in the specific place that matters. Fixed by reading
the specific bullet the claim depends on.

**How to apply:** when a guard's job is "this document says the correct
thing", write it as "no file in scope says something *inconsistent* with the
source of truth" (discovery + a NOT-wrong check across every file), never as
"the right string appears" (satisfied by the first match anywhere). Red-test
by replaying the actual originating defect (restore the stale value in the
*second* file) — a guard that only catches the first file's staleness has
already shown that failure mode once.

Related: [[feedback_split_contract_needs_parity]],
[[feedback_hand_copied_pairs_need_bidirectional_guards]],
[[feedback_pin_known_defect_not_xfail]],
[[feedback_static_guard_cannot_replace_an_invariant]].
