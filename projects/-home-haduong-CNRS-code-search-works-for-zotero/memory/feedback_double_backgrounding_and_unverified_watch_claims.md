---
name: feedback-double-backgrounding-and-unverified-watch-claims
description: "Don't combine nohup/& with the Bash tool's own run_in_background — it tracks the launcher forking, not the job; and don't trust an agent's 'silence means it passed' self-armed watch once it shows no live children in ListAgents"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ec860e90-d36f-4a14-9411-bfed986e87e4
  modified: 2026-09-14T04:11:01.429Z
---

Two related mistakes from the same evening (2026-09-13/14, closing tickets
0744/0760 in `search-works-for-zotero`), both about trusting a claim of
completion instead of observing it.

**Double-backgrounding produces a misleading "exit 0".** I ran
`nohup make check > log 2>&1 &` as the Bash tool command *and* passed
`run_in_background: true`. The outer shell forks the nohup'd process and
returns almost immediately; the tool tracked *that* trivial launcher exiting
0, not the real `make check` (which takes hours and was killed or orphaned
when the tracked command's process group tore down — the log cut off mid-way
with no error). The task-notification still said "completed (exit code 0)",
which read as a real result and wasn't. Diagnosed by checking
`ps aux` for the actual process (found nothing) and re-reading the log (cut
off at 27 lines with no summary or error).

**Fix:** never combine manual `&`/`nohup` backgrounding with
`run_in_background: true` — pass the foreground command directly
(`make check`, no trailing `&`) and let the tool handle backgrounding. It
tracks the real process and its real exit code.

**An agent's self-armed "I'll watch this and tell you if it fails" does not
survive its own turn ending.** A delegated team-lead merged a PR ahead of a
still-running mutation-test gate, justified by a diff argument, and said it
"armed a background watch" on the bypassed run — "silence means it passed."
By the time that watch would have reported, `ListAgents` showed the agent
`completed` with no live children: the watch was gone, not silent-because-
passing. Treating silence as confirmation here would have been exactly the
"an all-clear indistinguishable from I could not look" trap
(`rules/workflow.md`). The agent's own later-arriving notification did
eventually self-report a real result (EXIT=0), but that was luck of timing,
not a property I could have relied on — and an independently-run `make check`
against the actual merged tip, done in parallel, was the one result actually
verified from scratch.

**How to apply:** before accepting "I've armed a watch, silence means good,"
check `ListAgents` for that agent's live children — no live children means no
watch is actually running, regardless of what it said. When a load-bearing
gate result is unverified, run it yourself (via the tool's own
`run_in_background`, not a hand-rolled one) rather than wait on a promise
from a process that may no longer exist.

Related: [[feedback-verify-the-load-bearing-claim]],
[[feedback_positive_control_before_waiting]],
[[feedback-executor-gate-loop-stall]].
