---
name: feedback-concurrent-pipelines-shared-tickets
description: Root cause of the 2026-06-10 raid collisions — a terminal /raid and a claude.ai/code web session worked the same ticket store with no lock
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 96516ff3-e9dd-43d9-94cc-9744a7da7120
---

The 2026-06-10 raid burned real time/money on repeated 0512 collisions. The user
asked for a serious root-cause investigation; this is the verdict (two suspects
exonerated by evidence, the real cause confirmed):

**Real cause — two independent Claude pipelines on one shared ticket store, no
claim/lock.** A terminal `/raid` (this session) and a **claude.ai/code web
session** (id `session_012LdQi8…`, tracked via `tN` `/start-ticket` worktrees
`t0512`/`t0512b`) both picked up open ticket 0512 in parallel. The web session
did the reconciliation + opened PR #926; my session spawned redundant sub-agents
(finisher, reconciler) against work that was already underway. Detection was only
post-hoc (git/process forensics). Optimistic concurrency is the *intended* model
(per the user: "clean distributed development"); what failed is the reconciliation
discipline, not the existence of two workers.

**Suspects ruled out by evidence:**
- *CLI auto-update (2.1.169→170 that morning):* EXONERATED. A throwaway
  `isolation:worktree` probe based off `origin/main` (fresh) correctly, not stale
  local main. Not a base-ref regression.
- *Harness autonomous pipeline (beat/nightbeat/cron):* EXONERATED. `on-start.sh`
  doesn't auto-launch raids; no loop/cron fired; the web session was a manually
  launched slash-command session.
- *The web session had no harness:* a `claude.ai/code` session loads the PROJECT
  config but NOT user-global `~/.claude` (git.md fetch/rebase discipline), so it
  branched stale and resurrected closed tickets. Filed as the need to deliver the
  harness git-hygiene to web sessions.

**How to apply (the three disciplines that make optimistic concurrency safe):**
1. **Fetch-fresh base before branching** — "fresh"=local `refs/remotes/origin/main`,
   only as current as your last `git fetch`; after a `gh`/API merge of a dependency,
   `git fetch` BEFORE launching the next agent (this session skipped it → the 0512
   stale-base mess). 2. **Rebase onto current origin/main before merge** — never
   let a merge revert a sibling's committed work (#927 nearly resurrected closed
   tickets). 3. **A "no-revert-closed-ticket" merge guard** would catch the clobber
   automatically — harness-improvement candidate. Also: don't spawn redundant
   sub-agents on a ticket without first checking `git worktree list` + processes
   for another worker. See [[feedback_raid_wave_stale_base]],
   [[feedback_worktree_agent_env_leak]], [[feedback_concurrent_author_session_raids]].
