---
name: housekeeping
description: Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps.
user-invocable: true
argument-hint:
---

# Housekeeping

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

1. **Git phase.**
   - If `BEAT_HOUSEKEEPING_BRANCH` is **not** set (interactive run): `Bash(scripts/housekeeping-git.sh)` from the project root.
   - If `BEAT_HOUSEKEEPING_BRANCH` **is** set (beat.py run): skip — beat.py already ran the git phase before invoking this skill.

1.5. **GC stale agent worktrees.** Remove leftover `agent-*` worktrees whose branch is merged-and-gone (intact dirs that `git worktree prune` misses):
   ```bash
   ~/.claude/scripts/worktree-gc.sh
   ```
   Skips any worktree with uncommitted changes, never `rm -rf`s, silent when there is nothing to clean. Safe here because step 0 already confirmed no other live session, and the git phase above ran `git fetch --prune` so gone branches are detectable. See ticket 0169.

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
   pass: call `/ticket-close <id> already-done`. Log each closure as a
   fix-now action and include it in the step 3 commit. If *any* criterion
   is vague or cannot be reduced to these shapes → leave the ticket open.

   Process all open tickets unconditionally (not just candidates).
   Batch-closing is allowed here: close every qualifying ticket in one pass.

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
   - If no existing ticket covers it, create one with /ticket-new using a
     specific title. For test failures, the slug must contain `fix-tests`
     (e.g. `0042-fix-tests-module-not-found`).
   - If a ticket already exists, skip.

5. **Log `skip` items.** One line each, no action.

6. **Timestamp.** Update STATE.md to note the housekeeping run UTC date and time, commit it.

7. **Report.** Summarize what you did.

## Beat mode

When `BEAT_HOUSEKEEPING_BRANCH` is set in the environment, you are running
under `beat.py` on a dedicated `claude/housekeeping-*` branch already cut
from the remote default branch. Behaviour stays the same — commit fix-now
items and the timestamp as usual. Do NOT push or open a PR yourself.
`beat.py` checks for commits after you exit: if there are none it deletes
the branch; if there are commits it leaves the branch locally as a
"deferred" candidate for human review.

If `BEAT_HOUSEKEEPING_BRANCH` is unset (interactive `/housekeeping`), commit
in place as before — no PR detour for hand-typed runs.
