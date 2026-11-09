# Ten-ticket raid: author decisions

Commissioned 2026-11-07 in this session: 1442, 1453, 1454, 1455, 1456,
1457, 1459, 1460, 1450, and 1446. This brief records the author's corrections
to the older ticket bodies; these decisions take precedence.

- 1456: improve filename-derived Zotero searches, but an unsuccessful
  filename-only search is unidentified, never absent. Avoid an elaborate parser.
- 1457: allow tracked project bibliographies, with DOI/URL reader routes;
  Zotero remains authoritative and source documents stay outside git.
- 1442: interruption means execution stopped and the last outside action's
  outcome is uncertain. Check that action only before retrying it. No check
  before every command, ordinary pause, message, or known-complete action.
- 1453: use the existing standard-library policy. Dependency inspection is a
  harness-doctor diagnostic responsibility. No new rules or routine gate.
- 1454: investigate instructions that call helpers for missing/unavailable/
  failing helper recovery. Transcript evidence is supplementary and absence
  of transcripts is not proof that fallbacks work. Add a manual route only
  where the diagnostic establishes a gap; no universal fallback rewrite.
- 1455: existing instructions already distinguish missing evidence from false.
  Diagnose transcript instances of unknown becoming false, zero, absence, or
  all-clear. No additional general rule. An empty bounded audit is valid.
- 1459: find where language choice happens (Imagine or Plan or elsewhere),
  and inspect historical choices for concrete trouble a better choice would
  have avoided. Correct only on evidence; no new blanket language rule.
- 1460: redundant CLI-wrapper skills are a harness-doctor diagnostic, not a
  skill-builder rule. Identify actual added decisions/checks/recovery before
  proposing deletion; do not purge skills by title or command count.
- These audits remain reusable tools in the doctor's diagnostic toolkit,
  invoked for named concerns; never routine health checks, scheduled sweeps,
  or merge gates. Preserve evidence limits and positive controls.
- 1450: list no-forge notes review requests, preserving unreadable vs empty
  and explicit abandonment. Mention capability/limits for ticket 1445.
- 1446: clean-tree precondition for yawn, existing author-approved test-target
  contract, isolated test-doctor probe, diagnostic only. The ticket's one-time
  project sweep is commissioned separately from routine health checks; report
  projects without stores and ticket offenders in their own stores.

Use the existing raid → hunt → gaze → verify-gate → merge → roar cycle.
The doctor audits reuse harness-doctor; test-target diagnostics reuse
test-doctor; transcript access reuses existing trace tooling where suitable.
Do not create a new orchestration framework. Tracker 1444's inventory and
children must be reconciled with these decisions, without counting the
tracker as an extra implementation unit. Preserve user decisions rather
than forcing obsolete pilot/extra-rule criteria through the gate.

## Execution sequence

1446 is decomposed into 1462 (harness fix/probe) and 1463 (dependent one-time
sweep); the parent remains open until both and their integration review.

1. 1453, 1456, 1462: distinct source/test surfaces.
2. 1454, 1457, 1450: doctor reference, Zotero prose, notes listing.
3. 1455, 1442: doctor reference and uncertain-action recovery.
4. 1459: language-choice diagnostic.
5. 1460: wrapper-skill diagnostic.
6. 1463: one-time project sweep, after competing test suites finish.

Doctor reference changes are serial. Any concrete recovery correction from
1454 reserves its paths before implementation if it overlaps another unit.
No identified registry receives three concurrent PR edits in these waves.
1444 closes only after 1453/1454/1455 and integration review.

Blind-spot controls: listing excludes adopted forge review units; dirty-tree
nonexecution applies to all test runners, not just Make. The Zotero endpoint
initially failed under sandbox permission denial; this is not evidence that
the user's service is down. Existing private Zotero/Xvfb fixtures are reused.
