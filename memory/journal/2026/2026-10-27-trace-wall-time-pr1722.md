# trace-wall-time lands in trace-doctor (PR #1722)

**Context.** The author asked where raid, hunt and gaze spend wall time
(generation, testing, waiting), how much testing is redundant, and what
blocks; then asked to give the tool to /trace-doctor. Session ran from the
arena checkout; the PR lives in the harness (MinhHaDuong/ImperialDragonHarness#1722).

**Events.**
- First decomposition put 40-53% of wall in a "harness" bucket. Cause
  isolated: passive records (attachments, meta user records, system notes)
  are stamped with the next event; reattributing them to the next decisive
  record removed the bucket.
- /gaze 1722 launched from the arena cwd (local-only, no remote) escalated:
  no PR 1722 there. Relaunched with the full PR URL and the harness path.
- Three /gaze rounds: round 1 nine non-blocking findings (redundant tests
  undercounted by a test's own `> x.log` redirect and by `git merge-base`;
  --projects vs --projects-dir; pre-start agents; p90 on small n; raw
  command text in blockers); round 2 the credential fix partial (second
  argument word printed); round 3 one blocking item, a test that did not pin
  the nested-hunt fix.
- The author declined a fourth /gaze and directed the main session to verify
  the test-only commit (passes on ef5046f, fails on 69a1f95's script).
  /verify-gate refused (ESCALATE, no round spent): no /gaze result on the
  head, and an author instruction relayed by an agent is not approval.
- The author approved merging over the ESCALATE in session. Gate record
  passed on candidate 9ac73a7; merged pinned to ef5046f. Duration of the
  merge recipe 15m46s.
- At /roar the author said to skip review attribution ("it is broken");
  attribution_record.py --capture-pr 1722 had printed "missing or
  unexpected identity field".

**Outcome.** scripts/trace-wall-time.py on main, run by /trace-doctor step 1.
After the redirect fix, 7-day hunts: 36% of test runs, 27% of test minutes
were reruns with no change in between (first 28-day reading had been ~18%).
