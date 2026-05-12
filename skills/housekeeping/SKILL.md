---
name: housekeeping
description: Repo housekeeping — git sync, healthcheck, eager fix-now repairs, and ticket creation for open-ticket findings. Safe to call interactively or from automated sweeps.
user-invocable: true
argument-hint:
---

# Housekeeping

Run full repo housekeeping and act on every finding.

## Steps

1. **Git phase.**
   - If `BEAT_HOUSEKEEPING_BRANCH` is **not** set (interactive run): `Bash(scripts/housekeeping-git.sh)` from the project root.
   - If `BEAT_HOUSEKEEPING_BRANCH` **is** set (beat.py run): skip — beat.py already ran the git phase before invoking this skill.

2. **Healthcheck.** Invoke /healthcheck. The probe (`project-state.py`)
   runs once inside healthcheck and covers all checks — do not re-run git
   commands already collected there. Parse the **Action plan** section from
   the output: the bold headings `**fix-now**`, `**open-ticket**`, `**skip**`
   are the contract interface consumed by steps 3–5 below.

3. **Fix `fix-now` items.** Apply every `fix-now` item inline. If any fixes were
   applied, commit once: `chore: housekeeping fixes (sweep)`.

   **Branch deletion (fix-now from healthcheck check 4):** When a fix-now bullet says
   to delete a branch, apply these guards before acting. Skip (log a warning) if any
   guard trips:
   - **Open PR guard**: `gh pr list --head <branch> --json number | jq 'length > 0'` —
     skip if `true` (branch has an open PR).
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
