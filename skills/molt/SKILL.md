---
metadata:
  category: session
name: molt
description: "Repo housekeeping that acts: git sync, yawn, fix-now repairs, tickets for findings. Safe interactively or in automated sweeps. Not for a plain check (/yawn)."
user-invocable: true
argument-hint:
---

Bounded, mostly mechanical housekeeping; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Molt — repo housekeeping

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Run full repo housekeeping and act on every finding.

## Steps

0. **Active-session guard.** Before doing anything else, check for other live Claude sessions on this repo:

   ```bash
   git worktree list --porcelain | grep -E '^(worktree|locked|reason)' 
   ```

   For each worktree entry that has a `locked` line, extract the PID from the reason (format: `claude agent <name> (pid <N>)`):

   ```bash
   ps -p <N> -o pid= 2>/dev/null
   ```

   If **any** locked worktree has a live PID, **stop immediately** — print:

   ```
   ⚠ Housekeeping aborted: another Claude session is active (pid <N>, branch <branch>).
   Locked worktrees: <list>
   Re-run housekeeping after that session exits.
   ```

   Do not proceed past step 0. The fix-now deletions would race with the other session's uncommitted work.

0.7. **Freshen the erg binary (before any erg check).** Refresh the installed
   `erg` *before* step 1's git phase, because both erg-driven surfaces a sweep
   acts on run against whatever binary is on `PATH`: the corpus check
   `erg check tickets/` inside `housekeeping-git.sh`, and `erg ready` inside the
   step-2 yawn probe (`project-state.py` prefers `which erg`). A stale
   installed binary produces *false* violations on tickets using format the old
   binary predates (for example bogus hits on closed tickets carrying the
   newer `Label:` header), and an autonomous sweep would file
   tickets on them.

   ```bash
   erg update   # refresh the INSTALLED binary. Offline-safe by design: fetch
                # errors (no remote, no network, not a git repo) exit 0, so the
                # sweep never fails on an isolated machine.
   ```

   `erg update` only ever replaces the binary it runs as (the installed
   `~/.local/bin/erg`), never the committed `tickets/erg`. If a visited repo's
   committed `tickets/erg` lags its remote, **surface that as an `open-ticket`
   finding (step 4) — do not run `tickets/erg update` and do not commit a
   refreshed binary here.** The committed binary is durable state that travels
   via a merge request, not via a sweep's direct mutation.

   Ordering this before step 1 means every later erg-driven finding runs against
   the fresh binary: a violation that survives the refresh is real and may be
   ticketed; one that does not was a stale-binary artifact and is dropped.

1. **Git phase.** Run `"$IDH_ROOT/scripts/housekeeping-git.sh"` from the project root. Then cut a dated branch: `git switch -c housekeeping-$(date -u +%Y%m%d) origin/main`. All subsequent commits in this run land on that branch.

1.5. **GC stale worktrees.** Housekeeping owns worktree GC — but only of
   dead trees, never an active session's. Remove any registered worktree on an
   upstream-gone branch — regardless of path or name, including ones outside
   `.claude/worktrees/` (intact dirs that `git worktree prune` misses):
   ```bash
   "$IDH_ROOT/scripts/worktree-gc.sh"
   ```
   The script enforces the active-session rails itself (merged-and-pruned branches read `[gone]` while
   sessions still sit in them):
   it skips any worktree that is a live process's cwd, any locked worktree
   (lock = in use, mirroring step 0; only a dead-pid harness lock is
   unlocked, so the rails decide), any
   tree with uncommitted changes other than `.panel/` and `build/panel-head/`
   review scratch, and the one it runs from. Before clearing review scratch,
   each candidate with `.tmp/` must pass the merged-ancestry and readable
   citation gate across PR bodies, branch commits, and verdicts. A hit or
   unknown source retains `.tmp/` and the worktree as pending; eligible removal
   reports `.tmp/` size first. `.tmp/` is never purged independently. After
   that gate it purges only the two review-scratch paths, then reports and
   retains every other WIP file by name. It never `rm -rf`s a whole worktree and
   stays silent when there is nothing to report — but it also **reports
   (never removes) "husk" dirs** under `.claude/worktrees/` that are no longer
   registered worktrees (a session base cwd deregistered mid-session), so a
   `worktree-gc: husk …` line breaks the silence without anything being
   cleaned. That output is informational; report-only is the PERMANENT design
   (remote sessions are structurally undetectable, so no complete liveness
   signal exists) — do NOT re-file. **A worktree the
   GC skips for uncommitted changes is a signal, not just an obstacle:** diff
   it before moving on — orphaned WIP may be a closed ticket's dropped
   exit-criteria deliverable (`erg-pr-merge` autocloses on the `**Ticket:**`
   line unconditionally). If so,
   preserve (`wip(NNNN):` commit + push) and open a follow-up ticket.

1.7. **Sweep orphan session scratch directories.** Every session gets a scratch
   directory under the user's temp root and nothing but the `SessionEnd` hook
   removes one, so a crash, a kill, or a session that predates the hook leaves
   it behind — charged to the user's temp quota until the next fill kills the
   Bash tool in every session at once.

   ```bash
   python3 "$IDH_ROOT/scripts/session_scratch.py" --sweep
   ```

   The script owns the liveness rails and never removes a directory whose
   session has a live process: a live process holding an open descriptor inside
   it (the CLI keeps one on the session's `tasks/` directory for the session's
   whole life), a live process cwd'd inside it (the rail `worktree-gc.sh` uses),
   or the session id named by anything running. A directory touched in the
   last few minutes is skipped too, so a session that has just created its
   directory cannot be caught in the gap. It computes its own list rather than
   trusting the yawn's: a session can start between the two. Silent when
   there is nothing to remove; one line per directory otherwise, and it never
   exits non-zero. Nothing to commit — this is host state, not repo state.

   Add `--dry-run` to list without removing. The temp root itself is never
   relocated here: that is an operator decision (check 12 of the yawn
   names the knob).

2. **Yawn.** Invoke /yawn. The probe (`project-state.py`)
   runs once inside yawn and covers all checks — do not re-run git
   commands already collected there. Parse the **Action plan** section from
   the output: the bold headings `**fix-now**`, `**open-ticket**`, `**skip**`
   are the contract interface consumed by steps 3–5 below.

2.5. **Audit open-ticket exit criteria.** For each open ticket, apply
   lightweight grep-able checks. Only check exit criteria that reduce to one of
   three crisp shapes:

   1. **String absence**: `! grep -qF "<literal>" <file>`
   2. **File absence**: `test ! -f <path>`
   3. **Symbol presence**: `grep -qE '^(def|class|func) <name>' <file>`

   If *all* of a ticket's exit criteria reduce to these shapes AND all
   pass, run the following **as one shell command** for each qualifying ID.
   Keep the path lookup, close, and staging together: shell variables do not
   survive separate Bash tool calls.

   ```bash
   bash "$IDH_ROOT/skills/molt/ticket-sweep.sh" close <id>
   ```

   The script closes, then stages the closed file in one process. If it fails,
   stop the sweep and report the error; do not continue to archive or commit its
   partial edits. Exit 2 means `tickets/` or the erg binary is missing: skip
   the ticket sweep for this repository.

   Current `erg` moves the file on close; older `erg` leaves it at the source
   path until step 2.6 archives it. Log each closure as a fix-now
   action and include it in the step 3 commit. If *any* criterion is vague
   or cannot be reduced to these shapes → leave the ticket open.

   Process all open tickets unconditionally (not just candidates).
   Batch-closing is allowed here: close every qualifying ticket in one pass.

2.6. **Archive closed tickets.** Skip if `tickets/` is absent.

   ```bash
   bash "$IDH_ROOT/skills/molt/ticket-sweep.sh" archive
   ```

   The script moves any remaining ticket with a non-empty `Closed:` header from
   `tickets/` into `tickets/closed/` and stages exactly the paths the archive
   call reports (older `erg` leaves the file at the source path on close;
   current `erg` moves it). It then removes any file from `tickets/` that
   already exists in `tickets/closed/` (duplicate committed under both paths,
   possible independently of this sweep). Exit 2 means `tickets/` or the erg
   binary is missing: skip, do not treat it as a clean sweep.

   If any files were moved or removed, stage and include them in the step 3
   commit (`chore: housekeeping fixes (sweep)`). Do not create a separate
   commit for this step.

3. **Fix `fix-now` items.** Apply every `fix-now` item inline. If any fixes were
   applied, commit once: `chore: housekeeping fixes (sweep)`.

   **Branch deletion (fix-now from yawn check 4):** When a fix-now bullet says
   to delete a branch, apply these guards before acting. Skip (log a warning) if any
   guard trips:
   - **Merge guard**: re-run the merge probe from yawn check 4 and act on
     its exit status. Exit 0 → merged, deletion may proceed. Exit 1 → the branch
     is not merged, skip deletion. Exit 2 (`could-not-determine`) → the branch
     cannot be mapped to a landed merge request: skip deletion and log it; never
     read 2 as merged or as not merged.
     ```bash
     bash "$IDH_ROOT/skills/molt/ticket-sweep.sh" merged-probe <branch>
     ```
   - **Worktree guard**: if the branch is prefixed with `+` in `git branch` output, a
     worktree is checked out on it. Skip if the worktree is dirty (uncommitted changes).
     If the worktree is clean, run `"$IDH_ROOT/scripts/worktree-exit-preflight.sh" --removal --branch <branch> <path>` first. When `.tmp/` exists, this gate requires merged ancestry and clear, readable citation coverage across PR bodies, branch commits, and verdicts, then prints its size before removal. A citation hit, unreadable source, or uncertain ancestry keeps `.tmp/` and the worktree; report it as pending with the reason. `.tmp/` is never separately purged. Remove the worktree only after the gate passes.
   - **Safe delete**: use `git branch -d <branch>` (not `-D`) — this fails safely if
     the branch has unmerged commits, providing a final safety net.

4. **Ticket `open-ticket` items.** For each `open-ticket` finding:
   - Search open ticket slugs and titles for key terms from the finding.
   - If no existing ticket covers it, create one with `tickets/erg new "<title>"`
     using a specific title. For test failures, the slug must contain `fix-tests`
     (e.g. `0042-fix-tests-module-not-found`).
   - If a ticket already exists, skip.
   - Apply the severity floor (rules/workflow.md § Autonomous action), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.

5. **Log `skip` items.** One line each, no action.

6. **Open merge request.** If any commits were created in this run: push the branch (`git push -u origin HEAD`), open a merge request titled `chore: housekeeping sweep <date>`, include a `**Ticket:**` line only if a ticket tracks the run, and enable auto-merge so it lands after CI. If no commits were created: `git switch main && git branch -d housekeeping-$(date -u +%Y%m%d)` and skip the merge request.

7. **Report.** Summarize what you did.

## Branch discipline

Step 1 cuts a `housekeeping-<date>` branch from origin/main before any commits,
and step 6 pushes it and opens a merge request. All fixes land via that merge, never directly on main.
