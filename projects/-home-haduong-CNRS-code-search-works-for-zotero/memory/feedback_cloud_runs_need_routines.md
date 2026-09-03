---
name: feedback_cloud_runs_need_routines
description: "Agent isolation \"remote\" silently falls back to a local subagent; a real cloud run the author can follow from his phone is a RemoteTrigger routine with run_once_at"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 60570396-e466-44e8-862f-715e21d565aa
  modified: 2026-09-02T16:28:24.199Z
---

"Emerge those doable on a cloud" means a run visible in the Claude Code app,
not a background subagent. `Agent(isolation: "remote")` is **not** that path: it
is gated, and when unavailable it falls back to a local subagent **silently** —
the launch still reports "Async agent launched successfully" and hands back a
local `/tmp/claude-*/tasks/*.output` path. The author noticed before I did
("I don't see them in claude code app").

**Why:** the fallback is the failure mode this harness keeps meeting — an
all-clear indistinguishable from "I could not look". A successful-looking launch
is not evidence the work left the machine.

**How to apply:**

1. Verify, never assume. `ListAgents` shows a real fallback as
   `Subagents (n): … general-purpose · running`, with no cloud session listed.
   `TaskStop` confirms it by reporting `"task_type":"local_agent"`.
2. Kill the local fallbacks before relaunching, or two agents race into
   duplicate PRs on the fork.
3. Launch through the `schedule` skill → `RemoteTrigger action:"create"` with
   `run_once_at` a few minutes ahead (RFC3339 UTC, must be future; it fires once
   then auto-disables). `cron_expression` has a 1-hour minimum and is the wrong
   tool for "start now".
4. **Pass `body` as the structured parameter.** A hand-serialized raw JSON
   string gets truncated mid-prompt and fails to parse; it truncated at 4902,
   then 3441, then 2537 bytes on successive tries. Keep prompts compact and let
   the ticket file carry the detail.
5. **A cloud session starts with zero context and sees only the repos you
   attach.** `sources` is an array: attach both the code repo and the repo
   holding the tickets and spec, or the agent cannot read its own ticket. Here
   that is `MinhHaDuong/zoteus` plus `MinhHaDuong/search-works-for-zotero`.
6. It cannot reach this machine. Anything needing a local fixture or the live
   Zotero library stays local — see [[project_registry_not_knobs]] for what is
   machine-bound.
7. Environment: `env_01QgTtWtGfZCWmg3y6rNznBE`. Relay the routine URL
   (`https://claude.ai/code/routines/{id}`) so he can follow it; routines cannot
   be deleted from here, only at https://claude.ai/code/routines.

Restate the upstream read-only rule inside the cloud prompt itself
([[feedback_repo_prepares_upstream_it_ships_nothing]]): the cloud agent has no
`AGENTS.md` context loaded until it reads it, and it holds push rights.

## Reconnecting to a cloud session that is already running

A cloud session is **not** addressable through `ListAgents`/`SendMessage` from
a terminal session — it lists local peers only, and its absence there is not
evidence the run died. Reach it through `RemoteTrigger` instead:

1. `action:"list"` → find the routine (`persistent_session_id`, `last_fired_at`,
   `ended_reason: run_once_fired`). Parse the saved JSON with a script; the
   response is ~100 KB.
2. `action:"list_runs"` with its `trigger_id` → `status`, `worker_status`
   (`idle`/`running`), `last_event_at`, and the claude.ai URL. This is the cheap
   liveness probe; prefer it to re-reading the log.
3. `action:"get_run_log"` with the `session_id` → the condensed transcript,
   newest 200 events first (`cursor` pages *backwards*). Long results and final
   reports are truncated mid-text, so a finding can be unreadable from here —
   ask the session to restate it rather than guessing.
4. **To send it a message**, create a routine pinned to the live session:
   `persist_session: true`, `persistent_session_id: session_<id>` (note the
   `session_` prefix; `list_runs` reports the same id as `cse_<id>`),
   `run_once_at` two minutes out, and the prompt in
   `job_config.ccr.events[0].data.message`. It posts *into* that session, so
   `list_runs` shows **no new run row** — confirm delivery by `last_fired_at` on
   the routine plus `worker_status: running`, never by an empty run list.

**Why:** the session survives its routine. Both runs here were still `active`
two hours after firing, idle, each holding a question the author had never seen.
Nothing surfaces that; you have to go and look.

**How to apply:** when work is blocked on a cloud session, read its log before
redoing anything — twice today the answer was already there. Relay the author's
ruling as intent (goal, constraint, definition of done), not procedure, and
restate the standing constraints in the message: the session has been idle for
hours and its context may have compacted. Do work locally instead of relaying
when the cloud session's own token scope excludes the target — it said its
GitHub scope excluded `oscardvs/zoteus`, so the upstream filing was done from
this machine. See [[feedback_execute_authorized_outward_actions]] and
[[feedback_repo_prepares_upstream_it_ships_nothing]].
