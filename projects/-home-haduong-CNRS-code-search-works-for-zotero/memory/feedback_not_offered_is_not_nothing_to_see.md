---
name: feedback_not_offered_is_not_nothing_to_see
description: "A not-offered cell says the harness could not look, never that there was nothing to see; read the requirement's body before calling a gap instrument-only"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 23ae8345-4e0c-469c-8519-4d269f82e902
  modified: 2026-09-03T11:21:35.934Z
---

Asked whether zoteus needs uninstall and pause/resume, I answered from the
acceptance matrix: `not-offered` on uninstall, `pause` already present,
`resume` "owned by no requirement". All three were wrong, and the author caught
it by saying *let's reread the Reqs together*.

**Why:** I read each headline and skipped the body that carries the obligation.

- **R15** headline says "After uninstall, none of that state may remain" — which
  I read as satisfiable by any mechanism, so a user deleting the data directory
  counted. The body says *"the target's **real uninstall surface** removes
  them"*. And R23, in the same section, forbids exactly my workaround:
  "without anyone deleting files by hand".
- **R22**'s second clause ("MUST hold across restarts") I treated as satisfied.
  The adapter's note is an argument, not a measurement — the cancel flag is *in
  memory*, and it holds only because nothing auto-resumes; the run sets
  `ZOTEUS_INDEX_AUTO_REFRESH=false`, so **the configuration in which the clause
  could fail was switched off in the configuration that tested it**.
- **resume**: right that R22 does not ask for it, wrong that nothing does. R3
  does — the only way to continue an interrupted build is the full rebuild, which
  re-embeds bytes that did not change, i.e. cost proportional to the library.
  R4 too, since that action deletes an unreadable index first.

**How to apply:** before concluding a gap is the instrument's rather than the
product's, open the requirement and read past the first sentence — the promise's
mechanism obligations live in the body. And treat a clause as unmeasured, not
kept, when the arm that could falsify it is disabled in the run that "passed"
it. Same family as [[feedback_probe_needs_discriminating_control]] and
[[feedback_the_tickets_own_test_needs_a_control]]; the inverse of
[[feedback_mechanism_wearing_a_requirements_number]], where the defect was a
requirement naming a build — here it was me reading a build obligation *out* of
a requirement that states one.
