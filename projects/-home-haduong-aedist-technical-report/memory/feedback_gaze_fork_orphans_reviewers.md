---
name: feedback-gaze-fork-orphans-reviewers
description: "A forked /gaze can end its turn with reviewers still in flight — their results arrive later as task-notifications; don't relaunch immediately"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a7ab5764-47b2-427d-af56-e627422f2f08
---

During the 0538 raid (2026-06-11), `/gaze 977` (forked execution) returned with
"Waiting for all three to return" — the fork ended while its background
reviewers ran. The orchestrator assumed they were orphaned and relaunched an
equivalent reviewer battery. Minutes later the fork's original reviewers ALL
delivered via `<task-notification>` (one even posted its review to the PR),
yielding six review streams instead of three.

**Why:** background agents launched inside a fork keep running in the session;
their completions surface as task-notifications to the main loop.

**How to apply:** when a forked skill returns mid-flight ("waiting for X"),
pause one beat — check TaskList / wait for task-notifications — before
relaunching the work. Duplicate reviews are wasteful but benign; duplicate
EXECUTORS on one branch would violate the ping-pong rule. Silver lining:
double panels gave convergence evidence (3 reviewers independently caught the
same copula fragment).

Recurred identically in the 0540 raid (2026-06-11, /gaze 978, twice): both fork
invocations returned at fanout-start; ALL reviewer batteries (the two forks' +
the orchestrator's own fallback) later delivered via task-notifications — seven
review streams for one PR. The fork never delivers the gate verdict itself when
this happens: run `/verify-gate <pr>` directly once reviews are in, rather than
re-invoking /gaze a third time. Convergence again paid: only the widest panel
caught the two MAJORs (S-figure ref in body, contribution claim stranded in
annex).
