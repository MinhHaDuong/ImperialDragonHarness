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
