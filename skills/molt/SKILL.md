---
metadata:
  category: session
  order: 2
name: molt
description: "Repo housekeeping: git sync, yawn, fix-now repairs, tickets for findings. Safe interactively or in automated sweeps. Everything /roar missed. Not for a plain check (/yawn)."
user-invocable: true
argument-hint:
---

Bounded, mostly mechanical housekeeping; choose the worker per the `route` skill (`skills/route/SKILL.md`).

# Molt — repo housekeeping

Neighbouring skills and when to prefer each: [session-lifecycle](../lair/references/session-lifecycle.md).

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

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

   A lock with no checkable pid (none, pid 1, several, or past pid_max)
   names no owner: inside a pid namespace `$PPID` reads 1, and on the host
   pid 1 is init, always alive. Do not abort
   on it here; step 1.5's `worktree-gc.sh` reclaims the harness shapes
   (`(pid 1`, `(owner pid not visible)`) once the tree is clean and idle 72 h (`skills/hunt/references/worktree-lifecycle.md`),
   and yawn lists the rest for removal by hand.

   If **any** other locked worktree has a live PID, **stop immediately** — print:

   ```
   ⚠ Housekeeping aborted: another Claude session is active (pid <N>, branch <branch>).
   Locked worktrees: <list>
   Re-run housekeeping after that session exits.
   ```

   Do not proceed past step 0. The fix-now deletions would race with the other session's uncommitted work.

0.7. **The erg binary: the project's own, no refresh.** Every erg-driven
   surface a sweep acts on runs the project's vendored `tickets/erg`: the
   corpus check inside `housekeeping-git.sh`, `ticket-sweep.sh`, and `erg
   ready` inside the step-2 yawn probe (`project-state.py` prefers
   `tickets/erg` and falls back to `erg` on `PATH`). A stale binary produces
   *false* violations on tickets using format it predates (for example bogus
   hits on closed tickets carrying the newer `Label:` header), and an
   autonomous sweep would file tickets on them. Step 1 cuts the housekeeping
   branch from `origin/main`, which puts the project's reviewed binary in
   place; nothing needs refreshing first.

   **Do not run `erg sync` in a sweep** (`erg update` is its old name). It
   rewrites `tickets/erg` in place from the project's origin, and in a checkout
   whose local main lags, step 1's worktree cut then refuses the modified file
   even when it matches the target byte for byte. `erg sync --upstream`
   imports a binary the project has not reviewed: if a visited repo's
   committed `tickets/erg` lags git-erg, **surface that as an `open-ticket`
   finding (step 4) and do not commit a refreshed binary here.** The committed
   binary is durable state that travels via a merge request, not via a
   sweep's direct mutation. A stale `erg` on `PATH` is the operator's to
   reinstall; the sweep does not read it while `tickets/erg` exists.

1. **Git phase.** Run `"$IDH_ROOT/scripts/housekeeping-git.sh"`, then create the run's own worktree; the primary checkout stays on `main` for every parallel session and is never switched (`rules/git.md`). Use hunt's recipe (`skills/hunt/SKILL.md` § Worktree) with the branch `housekeeping-$(date -u +%Y%m%d)` cut from `origin/main`, the lock reason `molt housekeeping (pid <PPID>)`, and the path printed as `$W`; `cd "$W"` and register it with `worktree-tmp-guard.py`. Note `$W`: every later step runs in it, with absolute paths and `git -C "$W"`, and all commits land on that branch. Step 0 ran before this lock exists, and step 1.5 skips locked worktrees, so the run never GCs itself.

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
   (lock = in use, mirroring step 0; only a harness lock whose pid > 1 is
   dead is unlocked, and a harness owner-less lock on a clean tree idle 72 h
   is lifted at removal (`skills/hunt/references/worktree-lifecycle.md`), so
   the rails decide), any
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
   exit-criteria deliverable (a `**Ticket:**` claim closes its ticket at merge
   whatever landed). If so,
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

2. **Yawn.** If yawn already reported on this repository earlier in this
   conversation, check whether that report still holds before running it again:

   ```bash
   python3 "$IDH_ROOT/scripts/project-state.py" "$(git rev-parse --show-toplevel)" --fingerprint
   ```

   Equal to the report's `Probe fingerprint:` line → reuse its Action plan and
   skip the rerun; say so in the step 7 report. Different, `unavailable`, or no
   such line → the state has moved since: load the yawn skill. The fingerprint covers
   HEAD, the working tree, refs and worktrees, so a step 1 fetch that moved a
   ref or a step 1.5 removal forces the rerun. Molt's own branch cut does not,
   provided yawn ran on a checkout already at `origin/main`; from a lagging
   main or a feature branch the HEAD differs, and yawn runs again.

   With no earlier report, load the yawn skill. The probe (`project-state.py`)
   runs once inside yawn and covers all checks — do not re-run git
   commands already collected there. Parse the **Action plan** section from
   the output: the bold headings `**fix-now**`, `**open-ticket**`, `**skip**`
   are the contract interface consumed by steps 3–5 below. Yawn's closing
   `Next move:` line is addressed to a user who ran yawn alone; inside molt,
   ignore it: you are already in the move it suggests.

   Yawn check 14 findings (project directives shadowing the harness's) arrive
   as its JSON records; molt routes them and does not re-read local rules:
   `python3 "$IDH_ROOT/scripts/project_shadow.py" --plan < findings.jsonl`
   (`findings.jsonl` is the check 14 JSON lines, script output plus the judged
   findings) prints one plan line each; `fix-now:`, `open-ticket:` and
   `skip:` lines join the plan headings of the same name, and `report:` goes
   to the run summary only. Add `--auto` when `CLAUDE_NIGHT_SWEEP` is set.
   Dispositions come from yawn's judged pass; the script's mechanical records
   carry none, so they route to `skip:` for hand judgment. An `ok (reasoned)`
   finding yields no line: leave it alone.

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
   bash "$IDH_ROOT/scripts/ticket-sweep.sh" close <id>
   ```

   The script closes, then stages the closed file in one process. If it fails,
   stop the sweep (go to step 7 to release the worktree) and report the error; do not continue to archive or commit its
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
   bash "$IDH_ROOT/scripts/ticket-sweep.sh" archive
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
     bash "$IDH_ROOT/scripts/ticket-sweep.sh" merged-probe <branch>
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
   - A harness-bound finding is filed in the harness repo on a harness branch
     or worktree, never with `tickets/erg new` in the harness main checkout;
     an unattended sweep (`--auto`) only reports it. Project edits
     (`delete-local`, `annotate`) are `fix-now` commits on the step 1
     `housekeeping-<date>` branch.
   - Apply the severity floor (rules/workflow.md § Autonomous action), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.

5. **Log `skip` items.** One line each, no action.

6. **Open merge request.** If any commits were created in this run: push the branch (`git push -u origin HEAD`), open a merge request titled `chore: housekeeping sweep <date>`, include a `**Ticket:**` line only if a ticket tracks the run, and land it: on a gated base write the gate record and merge by the recipe (`skills/merge/SKILL.md` § Gated base), as one background command (a record missing after the base moved: record again on the same head); elsewhere enable auto-merge so it lands after CI. If no commits were created, skip the merge request; step 7 removes the worktree.

7. **Report and release the worktree.** This step runs on **every** exit after step 1: the normal path, step 2.5's stop-and-report, and a failure in any other step. `worktree-gc.sh` never reclaims a locked worktree on an unpushed branch, so a worktree left without commits hangs until someone removes it by hand. Before reporting:

   Shell variables do not survive Bash calls: read the literal worktree path printed at step 1 and use it verbatim; never run `git -C "$W"` with `$W` unset or unchecked.

   Check the cases in this order; the first that matches applies.

   1. **Dirty, blocked or holding scratch** (including step 2.5's stop, which leaves partial ticket edits): `<path>/.tmp` exists, or `"$IDH_ROOT/scripts/worktree-exit-preflight.sh" --removal --branch housekeeping-<date> <path>` exits non-zero. Keep the worktree and branch; name them and the blocker in the report. `.tmp/` is kept whatever the preflight says: it may clear uncited scratch, and a sweep's own notes are unread until the report.
   2. **Commits, merge request open or failed:** `git -C <path> rev-list --count origin/main..HEAD` is above 0 and the branch is not yet merged. Keep the worktree and branch; name both as pending until the merge (roar cleans them), with the push or merge-request failure if there was one.
   3. **No commits** (`git -C <path> rev-list --count origin/main..HEAD` is 0) and the preflight passed: from the primary checkout, `git worktree unlock <path> && git worktree remove <path> && git branch -d housekeeping-<date>`. If the sweep ran to the end, also record it for yawn check 8, which dates housekeeping from `git log` and sees no commit here: `touch "$(git rev-parse --path-format=absolute --git-common-dir)/molt-last-run"`. A stopped or crashed sweep records nothing: it did not finish.
   4. **Commits, merge request merged by step 6:** the branch is in `origin/main` (`git merge-base --is-ancestor <head> origin/main`). Remove as in case 3 (`git branch -d` also checks ancestry); roar's step 10 handles the remote branch.
   5. **Anything else** (a squash merge, an unfetched step-6 merge): keep the worktree and branch and name them; when in doubt, keep.

   Then summarize what you did, say which case applied, and propose: "Surface remaining nits?"

## Branch discipline

Step 1 cuts a `housekeeping-<date>` branch from origin/main in a dedicated worktree before any commits,
and step 6 pushes it and opens a merge request. All fixes land via that merge, never directly on main.
