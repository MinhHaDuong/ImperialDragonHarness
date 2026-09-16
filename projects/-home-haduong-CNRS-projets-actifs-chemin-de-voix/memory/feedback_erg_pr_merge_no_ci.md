---
name: erg-pr-merge-no-ci
description: erg-pr-merge CI-wait times out on repos with no checks — squash-merge already completed before the script dies
metadata:
  type: feedback
  originSessionId: t0217
---

`erg-pr-merge` step 2a runs `timeout 600 gh pr checks --watch` after pushing the ticket-close commit. On repos with no CI configured, `gh pr checks` never reports any results and the command times out after 600s, exiting non-zero.

**Why:** The script treats "no checks returned within 600s" the same as "CI failed." For repos without GitHub Actions, this always fires.

**How to apply:** When `erg-pr-merge` dies with "CI did not pass within 600s", check whether the PR is actually already merged (`gh pr view N --json state`). If `state == MERGED`, the squash-merge completed before the script exited — the worktree cleanup step ("master already used by worktree") is the real failure, which is harmless. If `state != MERGED`, run `gh pr merge N --squash` manually to complete step 3.

Linked: [[feedback_celebrate_squash_precheck]]
