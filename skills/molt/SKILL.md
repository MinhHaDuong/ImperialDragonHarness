---
name: molt
model: sonnet
effort: low
description: "Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps."
user-invocable: true
argument-hint:
---

# Molt — repo housekeeping

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

   Do not proceed past step 0. The fix-now deletions and STATE timestamp commit would race with the other session's uncommitted work.

   Exception: `BEAT_HOUSEKEEPING_BRANCH` is set — beat.py manages concurrency itself; skip this guard.

0.7. **Freshen the erg binary (before any erg check).** Refresh the installed
   `erg` *before* step 1's git phase, because both erg-driven surfaces a sweep
   acts on run against whatever binary is on `PATH`: the corpus check
   `erg check tickets/` inside `housekeeping-git.sh`, and `erg ready` inside the
   step-2 healthcheck probe (`project-state.py` prefers `which erg`). A stale
   installed binary produces *false* violations on tickets using format the old
   binary predates — six bogus folder/header hits on closed tickets carrying the
   newer `Label:` header, 2026-06-04 — and an autonomous sweep would file
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

1. **Git phase.**
   - If `BEAT_HOUSEKEEPING_BRANCH` is **not** set (interactive run): `Bash(~/.claude/scripts/housekeeping-git.sh)` from the project root. Then cut a dated branch: `git switch -c housekeeping-$(date -u +%Y%m%d) origin/main`. All subsequent commits in this run land on that branch.
   - If `BEAT_HOUSEKEEPING_BRANCH` **is** set (beat.py run): skip — beat.py already ran the git phase before invoking this skill.

1.5. **GC stale worktrees.** Housekeeping owns worktree GC — but only of
   dead trees, never an active session's. Remove any registered worktree on an
   upstream-gone branch — regardless of path or name, including ones outside
   `.claude/worktrees/` (intact dirs that `git worktree prune` misses):
   ```bash
   ~/.claude/scripts/worktree-gc.sh
   ```
   The script enforces the active-session rails itself (ticket 0355 — on
   2026-07-13 a rail-less GC removed two live sessions' base worktrees, whose
   merged-and-pruned branches read `[gone]` while sessions still sat in them):
   it skips any worktree that is a live process's cwd, any locked worktree
   (lock = in use, mirroring step 0's marker — never unlock-and-remove), any
   tree with uncommitted changes, and the one it runs from. It never `rm -rf`s
   and stays silent when there is nothing to report — but it also **reports
   (never removes) "husk" dirs** under `.claude/worktrees/` that are no longer
   registered worktrees (a session base cwd deregistered mid-session), so a
   `worktree-gc: husk …` line breaks the silence without anything being
   cleaned. That output is informational; report-only is the PERMANENT design
   (ticket 0338 closed the removal-heuristic question — remote sessions are
   structurally undetectable, so no complete liveness signal exists) — do NOT
   re-file. See tickets 0169, 0195, 0325, 0338. **A worktree the
   GC skips for uncommitted changes is a signal, not just an obstacle:** diff
   it before moving on — orphaned WIP may be a closed ticket's dropped
   exit-criteria deliverable (`erg-pr-merge` autocloses on the `**Ticket:**`
   line unconditionally; 2026-06-16 ticket 0609's mandated test sat
   uncommitted after PR #1111 closed it with only the data fix). If so,
   preserve (`wip(NNNN):` commit + push) and open a follow-up ticket.

1.7. **Sweep orphan session scratch directories.** Every session gets a scratch
   directory under the user's temp root and nothing but the `SessionEnd` hook
   removes one, so a crash, a kill, or a session that predates the hook leaves
   it behind — charged to the user's temp quota until the next fill kills the
   Bash tool in every session at once (2026-09-06: three sessions, then a
   reboot; ticket 0854).

   ```bash
   python3 ~/.claude/scripts/session_scratch.py --sweep
   ```

   The script owns the liveness rails and never removes a directory whose
   session has a live process: a live process holding an open descriptor inside
   it (the CLI keeps one on the session's `tasks/` directory for the session's
   whole life), a live process cwd'd inside it — the rail `worktree-gc.sh` uses
   — or the session id named by anything running. A directory touched in the
   last few minutes is skipped too, so a session that has just created its
   directory cannot be caught in the gap. It computes its own list rather than
   trusting the healthcheck's: a session can start between the two. Silent when
   there is nothing to remove; one line per directory otherwise, and it never
   exits non-zero. Nothing to commit — this is host state, not repo state.

   Add `--dry-run` to list without removing. The temp root itself is never
   relocated here: that is an operator decision (check 12 of the healthcheck
   names the knob).

2. **Healthcheck.** Invoke /healthcheck. The probe (`project-state.py`)
   runs once inside healthcheck and covers all checks — do not re-run git
   commands already collected there. Parse the **Action plan** section from
   the output: the bold headings `**fix-now**`, `**open-ticket**`, `**skip**`
   are the contract interface consumed by steps 3–5 below.

2.5. **Audit open-ticket exit criteria.** For each open ticket, apply the
   same lightweight grep-able checks used by /pick-ticket step 4. Only
   check exit criteria that reduce to one of three crisp shapes:

   1. **String absence**: `! grep -qF "<literal>" <file>`
   2. **File absence**: `test ! -f <path>`
   3. **Symbol presence**: `grep -qE '^(def|class|func) <name>' <file>`

   If *all* of a ticket's exit criteria reduce to these shapes AND all
   pass: run `erg close <id> already-done` (the close lands in the
   housekeeping branch's sweep commit). Log each closure as a fix-now
   action and include it in the step 3 commit. If *any* criterion is vague
   or cannot be reduced to these shapes → leave the ticket open.

   Process all open tickets unconditionally (not just candidates).
   Batch-closing is allowed here: close every qualifying ticket in one pass.

2.6. **Archive closed tickets.** Skip if `tickets/` is absent.

   ```bash
   # Stage exactly the files this archive moved (it prints `ARCHIVED <basename>`),
   # never the whole closed/ dir — a stray file there must not ride along.
   tickets/erg archive tickets/ | sed -n 's#^ARCHIVED #tickets/closed/#p' | xargs -r git add --
   ```

   This moves any ticket with a non-empty `Closed:` header from `tickets/`
   into `tickets/closed/`. After archiving, remove any file from `tickets/`
   that already exists in `tickets/closed/` (duplicate committed under both
   paths):

   ```bash
   shopt -s nullglob
   for f in tickets/*.erg; do
     base=$(basename "$f")
     if [ -f "tickets/closed/$base" ]; then
       git rm "$f"
     fi
   done
   shopt -u nullglob
   ```

   If any files were moved or removed, stage and include them in the step 3
   commit (`chore: housekeeping fixes (sweep)`). Do not create a separate
   commit for this step.

3. **Fix `fix-now` items.** Apply every `fix-now` item inline. If any fixes were
   applied, commit once: `chore: housekeeping fixes (sweep)`.

   **Branch deletion (fix-now from healthcheck check 4):** When a fix-now bullet says
   to delete a branch, apply these guards before acting. Skip (log a warning) if any
   guard trips:
   - **Merge guard**: re-run the merge probe from healthcheck check 4 and confirm
     it exits 0. If the ticket ID does NOT appear in main's commit log since the branch
     diverged, the branch is not yet merged — skip deletion.
     ```bash
     merge_base=$(git merge-base main <branch>)
     pr_num=$(grep -oP '^Closed:.*#\K[0-9]+' tickets/closed/$(ls tickets/closed/ | grep -P "^$(echo <branch> | grep -oP 't\K\d+')-" | head -1) 2>/dev/null | head -1 || true)
     [ -n "$pr_num" ] && git log $merge_base..main --format="%s%n%b" | grep -qE "\(#${pr_num}\)"
     ```
   - **Worktree guard**: if the branch is prefixed with `+` in `git branch` output, a
     worktree is checked out on it. Skip if the worktree is dirty (uncommitted changes).
     If the worktree is clean, remove it first with `git worktree remove <path>`.
   - **Safe delete**: use `git branch -d <branch>` (not `-D`) — this fails safely if
     the branch has unmerged commits, providing a final safety net.

4. **Ticket `open-ticket` items.** For each `open-ticket` finding:
   - Search open ticket slugs and titles for key terms from the finding.
   - If no existing ticket covers it, create one with `tickets/erg new "<title>"`
     using a specific title. For test failures, the slug must contain `fix-tests`
     (e.g. `0042-fix-tests-module-not-found`).
   - If a ticket already exists, skip.
   - Apply the severity floor (rules/workflow.md § Autonomous Action Rules), in every repo — findings that don't block a merge, corrupt state, or bite the science are reported in the run summary, not ticketed.

5. **Log `skip` items.** One line each, no action.

6. **Timestamp.** Update STATE.md to note the housekeeping run UTC date and time, commit it.

6.5. **Open merge request (interactive run only).** If `BEAT_HOUSEKEEPING_BRANCH` is unset and any commits were created in this run: push the branch (`git push -u origin HEAD`), open a merge request titled `chore: housekeeping sweep <date>`, include a `**Ticket:**` line only if a ticket tracks the run, and enable auto-merge so it lands after CI. If no commits were created: `git switch main && git branch -d housekeeping-$(date -u +%Y%m%d)` and skip the merge request.

7. **Report.** Summarize what you did.

## Beat mode

When `BEAT_HOUSEKEEPING_BRANCH` is set in the environment, you are running
under `beat.py` on a dedicated `claude/housekeeping-*` branch already cut
from the remote default branch. Behaviour stays the same — commit fix-now
items and the timestamp as usual. Do NOT push or open a PR yourself.
`beat.py` checks for commits after you exit: if there are none it deletes
the branch; if there are commits it leaves the branch locally as a
"deferred" candidate for human review.

If `BEAT_HOUSEKEEPING_BRANCH` is unset (interactive `/molt`), step 1
cuts a `housekeeping-<date>` branch from origin/main before any commits, and
step 6.5 pushes it and opens a merge request. All fixes — including the STATE
timestamp — land via that merge, never directly on main.
