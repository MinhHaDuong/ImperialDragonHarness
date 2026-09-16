---
name: feedback-a-checkbox-needs-its-procedure
description: "An exit-criteria box that names no procedure is tickable while the source asserts the opposite — write the grep into the box, and positive-control its narrow form"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 3cdf4883-8bf7-4ffa-8060-2e328114969d
  modified: 2026-09-15T21:27:33.399Z
---

A verification box in a handoff ticket is executed by someone who was not there
when it was written. If it says "SPEC no longer claims the old design" it will
be ticked by a reader who skimmed SPEC and saw nothing alarming. If it says
`grep -n "<the exact sentence>" SPEC.md` returns nothing, it cannot.

**Why:** on 2026-09-15, ticket 0797's Action 9 called the required SPEC edit "a
sentence". `SPEC.md`'s sitter passage in fact asserted the reversed design
across twenty lines, including one that was the exact inverse of the author's
ruling — "Zotero's plugin disable control … is no longer R22's control for the
sitter". The ticket's own verification bullet named no procedure, so it was
tickable while SPEC said the opposite of the shipped behaviour. The gate caught
it, in a ticket that cites the all-clear-indistinguishable-from-never-looked
trap three times elsewhere.

The follow-on is the sharper half. Rewritten with greps, one of the three still
lied: a sweep for `ENABLED_PREF` over `tests/ verification/ plugins/` returned
four files and claimed to be a complete roster. It missed four more. Two lay
outside the path list, in `bench/`; two lay **inside** it and were missed on the
pattern alone, carrying the preference string and never the JS constant. None of
the four reddens anything when it goes inert, because `make check-fast` is
`pytest tests/ -q` and never reaches `bench/`.

**How to apply:** put the command in the box, not the conclusion. Then run the
box's own command against the unfixed tree and count — a check that cannot fire
before the fix proves nothing after it, and a narrow sweep's failure mode is not
a zero but a plausible-looking roster with a hole in it. Widening `ENABLED_PREF`
to also match the pref string took the sweep from four files to nine; the four
that mattered were all in the difference. Where a grep genuinely cannot decide
something, pair it with a named site-by-site walk and say which half does which,
rather than letting the grep imply a completeness it does not have.

Same family as [[feedback_probe_needs_discriminating_control]], one level up:
that one governs an experiment's control, this one governs a checklist's.
See also [[feedback_line_citations_rot]], learned the same night.
