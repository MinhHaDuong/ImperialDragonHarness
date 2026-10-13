# Correctness — PR #1374, round 6

Anchor: `3a5fcb313cb952694e5d24f1acc2a938e511cb54`, base `refs/remotes/origin/main`; anchor helper passed before and after review; all ten changed paths read. Full proportional reset review against the author-corrected contract at PR comment 6144242041 and current ticket 1084 criteria.

Identity: requested model pin `gpt-6.1-sol`, medium effort (manifest). Runtime identifies this agent as GPT-6; provider/backend model identity is not independently attestable. Same OpenAI family as producer Sol6.1 medium: this seat is not independent. Cross-family independence belongs to the separate red-team seat. No gate or merge invoked; historical gate cap remains intact.

## Finding

**P1 — Unreadable Git metadata bypasses the worktree preflight. Confidence: high.**

At `skills/roar/close-and-clean.sh:139`, both `git rev-parse` calls run inside substitutions of an equality test, without their exit statuses being checked. If both fail, their empty stdout values compare equal. The wrapper reports `PREFLIGHT: skipped (not in a linked worktree)` and `RESULT: clean`, exits 0, and never calls the existing fail-closed preflight. This contradicts the could-not-look contract and can let the step-9 caller proceed toward exiting a dirty linked worktree with no cleanliness check.

Reproduced in isolated fixture `/tmp/correctness-1374-7_ym9dlj`: a real linked worktree `peer` contains untracked `uncommitted.txt`. Positive control, invoking the exact HEAD helper with `--phase preflight` and real Git, reports DIRTY and returns 1. A PATH wrapper that returns 128 for `git rev-parse` and delegates all other commands to `/usr/bin/git` produces:

```text
metadata unreadable
metadata unreadable
roar: PREFLIGHT: skipped (not in a linked worktree)
roar: RESULT: clean
exit: 0
```

The same false clean is reproducible from a directory outside a Git repository without fault injection. Check each metadata read successfully before comparing results; on failure report COULD-NOT-LOOK and return severity 2. Add coverage for unreadable metadata in the preflight phase (the existing rev-parse failure test covers only after-exit cleanup).

## Verification and scope

- Ran `bash /tmp/idh-review-1374-revision/tests/test_roar_close_and_clean.sh`: exit 0, all 87 assertions pass. In particular, late unmerged self-tracking tips are refused by native `-d` with command-local upstream disabled, and a late peer checkout triggers Git's worktree refusal. No deletion of those protected branches reproduced.
- Reviewed producer validation and `/tmp/revise-1374-full.log`: recorded full suite 1603 passed, 4 skipped. This is producer evidence, not a new full-suite run by this seat.
- Explicit full-OID targets, foreign merged-ref retention, independent local/remote targets, missing-target idempotence, exact remote-ref inspection beyond fetch scope, leased remote deletion, and no delete-and-restore implementation match the corrected completed-task contract. Fetch explicitly disables branch and tag pruning. The documented non-atomic prechecks do not warrant imposing a universal concurrency guarantee.
- Tickets 1089 discovery and 1090 future measurement are authorized scope. No post-merge performance measurement is claimed; the historical gate ledger remains in 1084.

Verdict: **request-changes**.
