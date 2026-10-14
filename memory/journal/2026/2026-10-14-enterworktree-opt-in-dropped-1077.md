# EnterWorktree opt-in dropped (1077) — 2026-10-14

Project: ImperialDragonHarness. Ticket 1077, PR #1407 (merged fa7789a3),
PR #1411 (closes 1097 as moot). Host padme, Claude Code, Opus 5.5 session.

## Events

- The experiment ran from a session that had not entered a worktree. The
  session Bash call, a background job and a non-isolated subagent each ran
  `git worktree add` with no refusal.
- Positive control: once the session entered its worktree
  (`EnterWorktree path=`), `git -C <primary> worktree add` was refused.
  A subagent spawned from the entered session was refused the same way.
- Plain `git worktree add/lock/unlock/remove`, without `-C` and run from
  inside the entered worktree, passed for the session and its subagent.
- `git -C <sibling worktree> rev-parse` and `cd <sibling> && git ...` were
  both refused: the guard admits only the session's own tree. Recommending
  "keep the guard, drop `-C` from hunt" had assumed otherwise. The finding
  reversed that recommendation before any code changed.
- The rules recommended `-C` in four places (git.md, workflow.md), all
  refused in an entered session.
- `$PPID` in a subagent's Bash is the session's own `claude` process. That
  process had lived 2h45 through `/clear`; a single-session process (the
  #1395 session, pid 3742738) was gone after its session ended.
- A parallel session had run the same experiment earlier (PR #1395), with
  an `isolation: worktree` subagent as its positive control. Its findings
  agreed. Its log entry was folded into #1407 and #1395 closed. Removing
  that session's worktree and branch was refused twice by the auto-mode
  permission classifier ("Git Destructive", "Interfere With Workloads"); the
  author ran the removal by hand.
- Author decision: drop the guard, no replacement guard. The author first
  asked whether that meant no isolation; the distinction drawn was between
  worktrees (kept, plain git) and the runtime's cwd move plus guard
  (removed).
- During implementation, a session restart reset the cwd to the primary
  checkout. A relative-path `sed` then edited `skills/lair/SKILL.md` on
  main. `/gaze` reported the dirty primary; the edit was moved to the
  branch and reversed on main. A later `cd ~/.cache/...` outside the
  project was reset by the runtime to the launch directory, not the
  worktree.
- `/gaze 1407`: round 1 REROLL (two stale references from the rename
  sweep), round 2 APPROVED; review worktree created and read with plain git
  and `git -C` from the un-entered session, no refusal. The author counted
  it as the review-tree demonstration and 1077 closed with the merge.

## Outcome

`rules/claude-code.md` entry is now hunt step 3's recipe (add, lock, `cd`)
and forbids `EnterWorktree`; `settings.shared.json` no longer pre-approves
`EnterWorktree`/`ExitWorktree`; roar 9b-c and lair 7 use plain git. Accepted
residual risk, recorded in the ticket: `restore`/`checkout` aimed at another
tree lose their only guard.
