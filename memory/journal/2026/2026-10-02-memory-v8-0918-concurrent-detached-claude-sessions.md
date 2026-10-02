# Two detached claude sessions ran concurrently in one trial clone

Context: memory-v8 acceptance trial (ticket 0918), conductor session preparing
the Claude Code leg in /tmp/mem0918/claude/clone on 2026-10-02.

Observation: the first detached claude launch failed immediately (its
--allowedTools flag consumed the positional prompt; claude -p exited 1 with
"Input must be provided either through stdin or as a prompt argument"). A
relaunch was prepared through a different launcher; the relaunch command was
sent through a shell call that itself timed out at the tool layer, and the
setsid session it had started kept running. Both the surviving setsid
session and the separately relaunched one then executed the same trial
prompt concurrently in the same clone. Four untracked journal entries
resulted: three written by the first session, and a fourth written by the
second, which found the first three, independently re-verified each of
their facts, declined to duplicate them, and recorded the non-independence
of its own results.

Consequence: no entry was lost or overwritten; the overlap was resolved
explicitly by the second session with no-capture verdicts citing the
existing entries. The double run was a launcher error by the conductor
(assuming a timed-out launcher call had killed its child), recorded here
as such; the surviving evidence for the claude leg is one full session
stream plus the second session's verification.

Evidence: /tmp/mem0918/claude/stream.jsonl (one session's record survived;
the other was truncated by the concurrent redirect), the four entries under
/tmp/mem0918/claude/clone/memory/journal/2026/, and the second session's
final report. Which session's stream survived is established by its
content; the truncated stream's session is identified only by its captures.
