---
name: feedback-ticket-id-collision-check
description: Fetch+check origin/main for highest ticket ID before picking a new one; collision discovery at merge time is expensive
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c5cea9fc-7d2c-4f74-9ce5-4a0a43ce75c3
---

Before creating a new ticket file, `git fetch origin --quiet && git ls-tree -r --name-only origin/main tickets/ | grep -oE '[0-9]{4}' | sort -un | tail -3` to find the highest committed ID on main. Pick max+1.

**Why:** The spec calls collision handling "optimistic" (`spec-erg-v1.md` "Coordination is out of scope"), and the pre-commit validator catches duplicates. But discovery at merge time is expensive: PR #379 (ticket 0195) collided with another agent's 0195-client-timeout-regression-class that landed on main while my branch was in flight. Recovery required renaming the file (`git mv` to 0197), patching PR body via `gh api` workaround (since `gh pr edit --body` is blocked here), and leaving the branch name + PR title mismatched. The validator would have caught the dup on merge, but at that point the cleanup is much messier than picking an unused ID up front.

**How to apply:**
- Before `Write` of a new `tickets/NNNN-*.erg`, run the fetch+ls-tree check.
- Local `ls tickets/*.erg tickets/closed/*.erg | sort | tail` is **not sufficient** — it misses tickets committed to origin/main after this worktree was created.
- If a collision is discovered post-PR, file the rename + comment trail on the PR (branch name and title may stay; the file path and PR body's `**Ticket:**` line are what matter for auto-close).

Related: [[feedback-gh-pr-edit-blocked]] documents the gh api workaround used in recovery.

**Second incident (2026-06-04):** ID 0412 allocated twice — a raid bundled its ticket on a PR branch (#698) while a parallel session committed 0412 directly to main. Even the fetch+check discipline cannot fully prevent this (the window is between check and merge); a duplicate then sat ON MAIN with `erg check` failing and zero CI signal, because lint runs only the log-placement validator and the chore-bypass path filter skips lint on tickets-only diffs. Mechanical gate ticketed: 0418 (erg check in CI). Recovery cost stayed low (one git mv + chore PR #701) because the collision was caught the same day — check `erg check tickets/` after every fetch when working ticket-heavy sessions.
