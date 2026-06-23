---
name: feedback-merge-workflow
description: "Lessons from squash-merge + worktree workflow — branch divergence, guard hook, erg-pr-merge sequence"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: be1e835b-17e0-441d-84ec-bcb75c0f8549
---

After a squash merge, local main diverges (6 ahead, 1 behind). `git reset --hard origin/main` is blocked by the guard hook even with a clean working tree. The fix is to ask the user to run `! git -C <project> reset --hard origin/main` in the terminal.

**Why:** The guard-destructive-bash.sh hook pattern-matches on `git reset --hard` without checking git status first.

**How to apply:** When local main diverges after a squash merge and the tree is clean, proactively tell the user to run the reset via `!` prefix rather than trying multiple workarounds.

Also: `erg-pr-merge` runs in the agent's worktree on the PR branch. If the verify agent pushed commits to the branch after the execution agent finished, a `git pull --rebase` in the agent worktree is needed before `erg-pr-merge` can push the ticket-close commit.

**erg-pr-merge corrupts dependent tickets (2026-06-19, PR #7).** When a PR closes a ticket that is a `Blocked-by:` of still-open tickets, `erg-pr-merge` edits those dependents to drop the `Blocked-by:` header — but it produced a malformed ticket *missing the `--- log ---` separator* (the created log line was left bare between headers and `--- body ---`). That broke the *next* close in the same run (`close: missing '--- log ---' separator`), and the script is not idempotent past its committed closes. Recovery: re-insert `--- log ---` before the orphaned log line in each touched dependent, `erg check` until PASS, then `erg close <id> "<reason>"` the missed ticket + `git mv` it into `closed/`, commit, and `gh pr merge` directly (do NOT re-run erg-pr-merge). Separately, the *committed* `tickets/erg` bootstrap binary rejected the `Label:` header (`unknown header 'Label'`) and lacked `list` — it was simply **stale vs the installed `~/.local/bin/erg`**. **Resolved 2026-06-23 (ticket 0027):** `tickets/erg update` (→ build 2026-06-18) restored `Label:`/`list`; `erg migrate` then converted the whole store `Tag:`→`Label:`. Lesson: when an erg subcommand/header "doesn't exist," suspect a stale *committed* bootstrap binary before assuming a real erg bug — diff `./tickets/erg version` against `~/.local/bin/erg`, and keep the committed one current (it also feeds `refresh-STATE.py`). The dependent-ticket-corruption bug above was not reproduced this session.

See also: [[feedback-worktree-isolation]]
