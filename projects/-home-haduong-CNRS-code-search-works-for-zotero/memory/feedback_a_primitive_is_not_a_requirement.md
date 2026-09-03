---
name: feedback_a_primitive_is_not_a_requirement
description: "A function existing in the codebase is not the requirement being met; check what calls it, on what path, under what caps"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c34e2a1c-bfb3-41ee-9717-feaba5182542
  modified: 2026-09-03T10:46:56.278Z
---

Finding the function is the easy half. Whether the requirement is *met* depends
on what calls it, on which path, and under what limits — and that is a separate
read, in a different file, that is easy to skip once the grep has produced
something satisfying.

Worked example, 2026-09-03, caught by an independent reviewer and not by me.
`extractPdfPages` exists in the fork and really does re-extract exact page
ranges through pdf.js, so R24 ("a hit MUST lead to the page it came from") was
reported met without an estimate and without a pack. Both halves were wrong:

- **Not wired.** `rankPassages` in `features/fulltext/passages.ts` sets only
  `pageApprox`, a proportional estimate. The exact page lives behind
  `zotero_get_fulltext` with `precise_pages:true` or a `page_range` — a
  separate opt-in call that no search hit makes. SPEC's own note says the
  body-hit contract stays `pageIsEstimate: true` until a verified exact
  mapping exists.
- **Capped.** `extractPdfPages` refuses above `DEFAULT_PRECISE_MAX_BYTES`
  (20 MB) and returns null, so the very benchmark document the argument rested
  on may sit outside it.

**Why:** this is the mirror of
[[feedback_search_the_fork_before_claiming_absence]] and the two failures
compound. That one says a null result is not an absence. This one says a hit is
not a capability. Both were made in the same session, in the same ticket, from
the same habit of letting a grep stand in for a read — and the second is more
dangerous, because a found symbol *feels* like evidence in a way an empty
result does not.

The cost is not only a wrong sentence. The claim was load-bearing for a design
argument about whether ticket 0606's pack route is worth 2,2x the bytes and
24,6 h, so an overstated incumbent would have decided a real question.

Distinguish it from its neighbour
[[read-the-code-before-designing-around-spec]], written the same day by another
session: there the mechanism was **unbuilt** and SPEC's prose was mistaken for
running code. Here the mechanism is **built** and still does not meet the
requirement, which is the harder case — the grep succeeds, the source is real,
and only the call path gives it away. Three variants of one habit fired in a
single day across two sessions, which is what makes it a class rather than a
slip.

**How to apply:** before writing that a requirement is met, answer three
questions in the code and name the file for each — *what calls this on the
default path?*, *what does the default path return when nobody opts in?*, and
*what are its caps and its null-returning branches?* Then check the
requirement's own text for an implementation note; here SPEC.md carried the
contract that settled it. And apply one hedge to all mechanisms of the same
shape: two functions doing text-matching against pdf.js output under the same
size cap do not deserve different confidence just because one was reached for
first. See also [[feedback_verify_the_load_bearing_claim]].
