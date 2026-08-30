---
name: feedback-executor-gate-loop-stall
description: An executor can stall re-requesting a review panel that already reported — the seat reports reach the orchestrator, so read them and take over rather than waiting
metadata:
  type: feedback
---

A raid executor working ticket 0261 opened its PR, ran a five-seat review panel,
and then hung for roughly an hour without pushing. Its last words on being
stopped: *"The review panel never posted. Re-invoking once before escalating."*
It had re-requested the panel repeatedly; the seats answered each time with
identical content, one of them noting it had now been asked twice
(2026-08-29, raid 240).

**The tell is visible from the orchestrator, and it is specific.** The seat
reports arrive as task notifications in the *parent* session — so the parent can
read every finding while the child believes nothing was posted. Duplicate seat
reports with identical content, arriving after a branch tip has stopped moving,
means the loop is churning rather than converging. That is different from an
agent legitimately taking a long time, which shows fresh output.

**Why it costs more than the hour:** the raid's timeout circuit-breaker keys on
"has not pushed in 10 minutes", and an agent spawning subagents that keep
completing *looks* alive by every other signal. So the breaker does not fire on
its own judgement — someone has to notice the content is repeating.

**How to apply:** when a child's review seats report to you twice with the same
content and its branch has not moved, stop waiting. The findings are already in
your context, which is the whole reason taking over is cheap: run
`worktree-salvage.sh` on its worktree first (here it came back clean, so nothing
was lost), stop the agent, then work the branch directly. Do not `SendMessage` a
correction — the redirect ban applies, and a child that has convinced itself its
panel never posted will not be argued out of it.

Taking over needs one mechanical detail: the child's branch is checked out in its
own worktree, so `git switch` to that name fails. Either check it out under a
distinct local name and push with `HEAD:<branch>`, or remove the dead worktree
first — `erg-pr-merge` requires the local branch name to match the PR's head, so
the rename has to happen before the merge step.

Related: [[feedback-preserve-agent-output]],
[[feedback-verify-the-load-bearing-claim]].
