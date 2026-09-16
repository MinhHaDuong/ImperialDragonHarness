---
name: non-vacuity-is-per-case
description: "A suite proven non-vacuous by mutation can still contain a case that cannot fail; non-vacuity is a property of each assertion and of one named property, never of the suite"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff375b61-7b76-4b82-bc1c-37f832cf70b0
  modified: 2026-09-16T09:35:04.714Z
---

Proving a test suite has teeth does not prove that any particular case in it
has teeth, and does not prove the suite can see the defect you care about now.
Non-vacuity is always relative to (a) the individual assertion and (b) one
named property. Three instances in a single raid, 2026-09-16:

- **A test that caught one regression and not its successor.** Ticket 0255's
  round-1 test asserted `rc == 0` and no leaked body line. A reviewer proved it
  non-vacuous by reverting the fix and watching it go red -- true, and I
  generalised it to "the tests bite". The round-2 red team then showed the same
  test passes against a *fail-open* bypass, because an escape-hatch PASS and a
  real PASS are both exit 0. It discriminated the old defect and was blind to
  the new one. Fix: assert the branch taken (the specific success message), not
  the exit code.
- **A case that could not fail at all.** Ticket 0256's
  `TestSlugifyNeverProducesClosedBasename/title_ending_in_the_word_closed`
  passed with and without the fix -- the 40-char truncation happened to cut
  before the suffix for that particular title. Its siblings caught the
  mutation, so the suite looked sound while that case was decorative.
- **A control testing the wrong term.** 0256's corpus-safety control claimed to
  prove the `!inClosedDir` guard protected the archive; the executor's own
  adherence pass found that `!hasClosed` was doing the protecting, so the
  control would have passed with the guard removed.

**Why:** a green suite reports an average. A reviewer who mutates *one* line
and sees red has proven that one line is covered, nothing more -- and the
natural next sentence ("so the tests are good") is the error. The failure is
attractive because it arrives attached to genuine evidence.

**How to apply:** when a review reports a suite non-vacuous, ask which property
it fired on, and whether that is the property now at stake. Mutate toward the
*new* worry, not the old one. For a case whose name states a property, check
that the fixture actually reaches the code path the name claims -- see
[[verify-premises-before-code]] and
[[redcontrol-no-cooperating-instrumentation]] for the same discipline applied
one level up.
