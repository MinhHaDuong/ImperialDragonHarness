# Session-lifecycle skills — which one, when

Shared by `/perch`, `/yawn`, `/molt`, `/roar`, `/lair`. Read the row for your
trigger; if another row fits better, switch.

| Skill | Trigger | Scope | Writes | Calls | Called by |
|-------|---------|-------|--------|-------|-----------|
| `/perch` | "where are we?" mid-session | this conversation | nothing (report only) | none | user |
| `/yawn` | "is the repo healthy?" | one repo, current state | nothing (fixes on request) | `project-state.py` probe | `/molt` step 2, user |
| `/molt` | housekeeping due, or after a sweep wants action | one repo | housekeeping branch, fix-now repairs, worktree GC, tickets | `/yawn`, `housekeeping-git.sh` | `/lair` step 1, automated sweeps, user |
| `/roar` | one PR just merged | the completed task only | memory facts, ticket close, that task's branch and worktree | none | user |
| `/lair` | the day is ending | every branch, the whole session | pushes, WIP commits, handoff comments, STATE refresh, metrics | `/molt`; proposes `/hoard` | user |

Memory neighbours, none of them lifecycle skills proper:

| Skill | Question it answers | Writes |
|-------|---------------------|--------|
| `/roar` capture step | what significant fact did this task produce? | append to the journal |
| `/memory-sweep` | which recorded claims have gone stale? | dated corrections, topic edits |
| `/hoard` | how do I tidy accumulated memory? | pruned and merged topics, index |

## Choosing between neighbours

- Read-only report wanted → `/perch` (conversation) or `/yawn` (repo).
- Repo needs acting on → `/molt`; never hand-run yawn's fix-now list.
- A PR just merged → `/roar`. The day is over → `/lair`. Roar never does
  repo-wide cleanup; lair never records task facts.
- Memory feels stale → `/memory-sweep`; memory feels bloated → `/hoard`;
  something new just happened → `/roar`.

## Redundancy review (recommendations only; nothing retired here)

- `/yawn` and `/molt`: **keep both.** One reports, one acts; molt reuses yawn's
  probe and its stable `fix-now` / `open-ticket` / `skip` contract.
- `/perch` and `/lair`: **keep both.** Perch writes nothing and needs no repo;
  lair's reflect step is a different, repo-backed job.
- `/lair` step 8 (stale worktrees, remote branches, orphan tickets) overlaps
  `/molt`, which already ran in step 1: **trim** lair step 8 to the leftovers
  molt cannot see.
- `/roar` and `/lair` both reflect: **keep**, scopes differ (one task, one day).
- `/memory-sweep` (32 lines) and `/hoard` both prune stale memory:
  **merge candidate**, as a `--audit` mode of hoard. The resident card saved
  is the argument; the cost is a longer hoard. Decide in a separate ticket.
