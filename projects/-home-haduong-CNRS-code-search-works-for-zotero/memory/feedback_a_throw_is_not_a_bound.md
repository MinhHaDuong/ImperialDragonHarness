---
name: feedback-a-throw-is-not-a-bound
description: A test that bounds an infinite loop with `throw` is disarmed when the code under test catches host errors and converts them to a terminal state — the runaway ends, and the test passes on the unfixed code
metadata:
  type: feedback
---

When a test bounds a potential infinite loop by having a stubbed callback
`throw` after N iterations, check what the code under test does with a throwing
callback. If it wraps that call in try/catch and maps the error onto a
**terminal** state, the throw does not fail the test — it *ends the very
runaway the test exists to detect*, the subject leaves the work queue, the run
completes, and every assertion passes against the unfixed code.

**Why.** search-works-for-zotero PR #576 (2026-09-15), sitter ticket 0792. The
fix bounded a re-pick loop that spun on an attachment whose identity changed on
every inspect. Its regression test made item 1's identity churn and, as the
bound, threw from `host.inspect` after 20 turns:

    if (++churn > 20) throw new Error('item 1 was re-picked without bound');

The scheduler's own `inspect()` helper catches everything the host throws and
returns `{ status: 'inspection-error' }`. That status is not in the queued
class, so `record()` → `refreshQueue()` dropped the item from `state.pending`,
the sweep finished, the queue moved on. Measured against `origin/main`'s
unfixed scheduler: the loop re-picked the item **501** times (ceiling imposed
by my probe), against the fixed loop's **2** — and the shipped test called both
of them green. The test comment asserted the opposite in good faith: *"without
it this test does not fail, it hangs"*. It never hung, because the code under
test defended itself against the instrument.

**The shape.** The instrument's abort signal travelled through the subject's own
error handling. A test's bound must not be expressible in a vocabulary the
subject is designed to swallow. This is one level below the usual "no positive
control" failure: a control was *attempted*, and the subject neutralised it.

**How to apply.** Bound the loop with a **terminal value the subject accepts
normally** — here, returning a settled status past a high ceiling — and make the
**count** the assertion:

    if (++churn > 50) return { status: 'current', identity: 'settled', ... };
    ...
    assert.ok(churn <= 3, `re-picked without bound: ${churn} inspections`);

Then run it against the unfixed tree and watch it go red before believing it:
repaired, it failed on `origin/main` with *"item 1 was re-picked without bound:
51 inspections"* and passed on the branch with 2. A mutation probe would not
have found this — the repo has one for this exact file — because a mutant proves
the suite catches an injected edit to the *code*, and this blind spot was in the
*test*. Nothing that mutates the subject can see a test that never fails.

Generally: for any loop-bounding or timeout-bounding test, ask *what does the
subject do with my abort signal?* before trusting the green.

Related: [[feedback-probe-needs-discriminating-control]] (a control must
discriminate), [[feedback-the-tickets-own-test-needs-a-control]] (run the
specified test against the defect first), [[feedback-hold-out-the-answer-key]].
