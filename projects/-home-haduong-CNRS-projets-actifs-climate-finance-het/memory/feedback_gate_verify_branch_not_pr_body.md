# Feedback: gate the actual branch state, not the PR description text

PR #1048 (ticket 0244, extend cited-works-availability guard to `_includes/`)
had a posted body claiming "test now fails: 3 citations lack fulltext, left
for author triage." Two later commits on the same branch (after the body was
written) resolved all three gaps with verified `file=` fields. The body was
never updated. A gate that trusted the description instead of running the
actual test at HEAD would have wrongly downgraded the verdict or bounced for
a non-issue.

**Lesson**: `/gaze`/`/verify-gate` (and any merge gate) must always run the
tests / read the diff at HEAD and treat the PR body as informational only,
never as evidence. Flag body staleness as a non-blocking nit for the author
to fix, not a merge blocker — git history is authoritative, the description
is not.

TTL: standing (applies to every future `/gaze` run, not project-specific).
