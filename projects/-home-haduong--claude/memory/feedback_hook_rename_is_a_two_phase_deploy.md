---
name: feedback_hook_rename_is_a_two_phase_deploy
description: "Renaming a hook script leaves the live settings.json pointing at a deleted file; the re-alignment moment is when the checkout carries the new file, not when the PR merges"
metadata:
  type: feedback
---

`~/.claude/settings.json` is **not** derived from the tracked
`settings.shared.json`. `scripts/check-settings-drift.sh` only *reports* the
difference and exits 0, and it already reports standing drift on `hooks`, so
nothing stops a machine from running a hook whose `command` names a script the
repo no longer has.

So a hook rename is a two-phase deploy, and the second phase is **not** the
merge. On 2026-09-10, right after PR #869 renamed
`block-pr-merge-in-worktree.sh` → `guard-gh-pr-merge.sh`, the obvious follow-up
looked like:

    sed -i 's#block-pr-merge-in-worktree.sh#guard-gh-pr-merge.sh#' ~/.claude/settings.json

Running it at that moment would have **broken the working hook**. The primary
checkout sat on an unrelated feature branch, not `main`: it still carried the
old file, so the live config was correct *for that tree*, and re-pointing it
would have named a file absent from the branch actually checked out.
`sync-local-main.sh` advances `main` by ref without touching whatever branch the
checkout has out, so a green merge says nothing about which script is on disk.

**How to apply:** before re-aligning a live hook path, check the file, not the
merge — `git rev-parse --abbrev-ref HEAD` in the primary checkout, then `ls` the
new path there. Re-align only once the new file exists on disk. Where a rename
is avoidable, weigh it against this: a name that lies costs a reader once, a
dangling hook pointer costs every session on every machine until someone
notices, and nothing fails loudly when it does.

Related: [[feedback_primary_checkout_staleness_gates_skills]],
[[feedback_measure_whether_a_guard_ever_fired]].
