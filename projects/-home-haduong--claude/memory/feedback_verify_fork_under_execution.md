---
name: verify-fork-under-execution
description: "Verify Skill forks can silently under-execute (no gate, no verdict, stale /tmp worktree) — orchestrator must check completion markers after every run"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a4011328-b36c-46b3-a9f3-3b58bc9408ce
---

During 0202's validation cycle (2026-06-04, raid 0203/0208), one of six
`/verify` fork runs (PR #274, run 1) returned a plausible-looking summary but
had skipped the gate, posted no verdict comment, left `/tmp/review-274`
behind, and never ran the containment postcondition. Not off-task — under-run.

**Why:** `context: fork` Skill invocations carry no enforcement that the
operating procedure completes; a fork can answer with a partial phase's output
and look done. Milder sibling of the [[rogue-agent-pattern]] drift modes.

**How to apply:** After every `/verify` fork returns, the orchestrator checks
three completion markers before accepting the result: (1) a verdict line
(APPROVED/REROLL/ESCALATE) exists, (2) the verdict comment is on the PR,
(3) `/tmp/review-<pr>` is gone. Any missing → clean up and retry once.
Deterministic fix ticketed as 0216 (Agent-spawn conversion with pinned cwd).
Positive signal from the same cycle: the permission guard DENIED an
out-of-role force-push from a verify fix loop — guard layers work.

Re-confirmed 2026-06-12 (raid 0253, PR #393) — after 0216/0228 closed: two
consecutive `/gaze` forks returned mid-run status text ("waiting for
reviewers") instead of a verdict; retry-once did NOT cure it. Working
fallback: the orchestrator collects the reviewer agents' results (they
arrive as task notifications) and runs `/verify-gate` directly with the
findings summarized in args — the gate completed and posted the verdict
comment first try.

Re-confirmed again 2026-09-10 (ticket 0900, PR #863), now for `/review-pr`:
both invocations returned "waiting on the panel" and never posted. The panel
itself ran fine — ten reviewers across the two calls, all returning real
verdicts including two `request-changes` that found a live gate bypass — but
the synthesis step never happened, so the verdicts existed only in task
notifications. The PR carried one review where it should have carried two.
Same fallback works and is now the expected path, not a rescue: collect the
reviewers' results from the notifications, synthesize, and post the review
yourself with `gh pr review --comment --body-file`. Check the PR's review
count before treating a round as done — a review that ran and never landed is
indistinguishable, from the PR page, from one that never ran.
