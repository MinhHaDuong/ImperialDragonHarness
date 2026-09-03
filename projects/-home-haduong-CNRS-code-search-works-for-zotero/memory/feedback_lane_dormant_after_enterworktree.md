---
name: feedback-lane-dormant-after-enterworktree
description: "A gate lane went dormant for 5h50m immediately after EnterWorktree and only an inbound message revived it; diagnose lane silence by transcript growth, not by forge artifacts"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d9122a0a-fb84-4ef0-be09-f46135ff7d71
  modified: 2026-09-03T04:00:49.001Z
---

**A silent lane is not necessarily a working lane, and not necessarily a dead
one. Measure before concluding.**

2026-09-03 overnight raid: a gate lane holding four PRs produced no forge
artifact for about six hours. Its transcript showed 37 tool calls total —
seven between 21:49:41 and 21:50:28, ending with `EnterWorktree`, then
**nothing until 03:40:07**, resuming within seconds of an inbound
`SendMessage`. It then worked correctly and fast. It never looped: a
repeated-fingerprint scan found one duplicate, and that one was legitimate.

**Cause, named by the lane itself in its final report.** It was not hung: it
spent roughly three hours **fighting the Bash guard**, which pins a session to
its original (shared) worktree even after `EnterWorktree`, and it **did not say
so**. Its own sentence is the lesson: *"A lead fighting a guard is
indistinguishable from a lead working."* My first reading — dormant at the
`EnterWorktree` call — was close but wrong in the way that matters: the calls
were failing, not absent, and a coordinator watching forge artifacts saw the
same nothing either way.

**The working shape, from that lane:** plain `git worktree add /tmp/<name>`
from the pinned tree, then `cd` into it. No `git -C` against the shared
checkout, no compound forms, and put the command in a script file once the
quoting gets complex. Brief gate and review lanes to work from `/tmp` and never
call `EnterWorktree`.

**How to diagnose, in order:**
1. **Measure transcript growth**, not forge activity. A lane can be generating
   hard while posting nothing. Use `stat -Lc %s` on the JSONL and sample twice
   — plain `stat` on the symlink reports the *link's* size (196 bytes) and
   silently answers a different question.
2. **Summarise tool-call shape, never content** — timestamps, tool names, short
   argument fingerprints. That reveals a dormancy gap and a loop without
   pulling the lane's output into the coordinator's context. Script kept at
   `~/.claude/jobs/*/tmp/inspect_agent.py`; rewrite it if gone, it is ~40 lines.
3. **A gap in timestamps is the tell.** Looping shows as repeated fingerprints;
   dormancy shows as one long interval with no calls at all. They need
   different remedies and look identical from outside.

**The remedy that worked: one message.** Cheap, non-destructive, and it revives
a dormant lane without losing its accumulated context — try it before
`TaskStop` + re-dispatch, which throws away hours of state. This is the
sibling of [[feedback_leads_park_on_untracked_background]]: there a lead waits
on a child it cannot hear; here it waits on nothing observable at all.

**Prophylactic:** tell gate and review lanes to work from `/tmp` rather than
calling `EnterWorktree`, which is what the healthy lanes did anyway.

Related: [[feedback_merge_authority_needs_attached_verdict]] (a reviewer's
completion notice lands at the parent, not the spawning lead) and
[[feedback_executor_gate_loop_stall]].
