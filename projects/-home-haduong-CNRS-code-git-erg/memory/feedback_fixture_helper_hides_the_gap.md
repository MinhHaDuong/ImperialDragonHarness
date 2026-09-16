---
name: feedback_fixture_helper_hides_the_gap
description: "When a test needs a helper to reach the code under test, ask what the helper is stepping around — that is often the defect."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a27d6179-c527-421f-a14a-e4de26d3f494
  modified: 2026-09-16T15:45:25.112Z
---

A fixture helper whose job is to get the test *to* the code under test is a
signal, not plumbing. Read it as a question: what does the code refuse to do
without this, and is that refusal correct?

Worked case, git-erg 2026-09-16. Ticket 0289's suite carried a `withTicket`
helper that wrote a dummy ticket into every fixture store, with the comment
"corpusWarnings and cmdCheck both return early on an empty corpus, so the store
needs one valid ticket for any of this to be reached." The helper was accurate
and the suite was green. What it was stepping around was the defect: `erg check`
skipped the whole asset enforcement on a store with no tickets -- i.e. for the
fresh adopter, the population the check exists for. A reviewer found it by
reading the helper rather than the assertions. A second instance surfaced the
same way one function over (PR #366).

**Why:** a green suite that reaches the code only via a helper proves the code
works *in the state the helper manufactures*. It says nothing about the state
the helper was invented to escape, and the comment explaining the helper is
usually a plain-language description of the bug.

**How to apply:**

- When writing a helper to make a fixture "work", write down why the code would
  not run without it, then ask whether a real user can be in the state you just
  engineered away. If yes, that is an arm, not a helper.
- When reviewing, read the fixture setup and its comments before the assertions.
- The repair is usually a deletion: in both git-erg cases the early return
  protected nothing, and removing it was the whole fix.

This is the fixture-shaped form of [[feedback_non_vacuity_is_per_case.md]] --
there the guard cannot fail; here it never runs. Both present as green.
