<!-- last-reviewed: 2026-06-04 -->
# Git Discipline

- **Always work on a branch.** Main is read-only — no exceptions. Everything (code, docs, tickets, STATE, memory, config) lands via branch + PR. See `rules/workflow.md` § Worktree paths.
- **One change per commit.** Message explains *why this change and not another*: alternatives considered, local design choices made.
- **Merge commits**: strategic-level detail — architecture decisions, cross-file impacts, residual debt. Feature merges go through merge requests; chores merge locally via short-lived branch + fast-forward.
- **Git is the project's long-term memory.** Top-level files reflect *now* — history lives in `git log`.
- **Worktree isolation is automatic** — the SessionStart hook enforces it. All worktrees are throwaway; branches hold durable state. Skills must not manually delete worktrees created via `Agent(isolation:"worktree")` — use `git worktree prune` after branch deletion, never `rm -rf`.
- **Never round-trip through `git stash` in a shared checkout.** The stash stack is repo-global — shared by every worktree and session. On a clean tree `git stash` saves nothing, so the following `pop` grabs *someone else's* stash (this resurrected a deleted ticket file on 2026-06-03, ticket 0193); a conflicted `pop` silently *retains* the entry, re-arming the trap. Need a clean baseline? Use a throwaway `git worktree add` or a WIP commit. If you must stash, use `git stash push -m <name>`, pop only after confirming `git stash list` shows your entry on top, and `git stash drop` it on conflict after resolving.
- **Squash merge is disabled.** This repo uses regular merge commits only (`--merge`). `git merge-base --is-ancestor` works correctly. For branches that may have been squash-merged historically (before 2026-05-25), verify via `gh pr view --json headRefName,mergeCommit` instead of `git cherry`.
- **Create a merge request** for each ticket to review changes before merging. Include one or more `**Ticket:** tickets/NNNN-...` lines in the PR body so `erg-pr-merge` can auto-close the ticket(s) on merge. Use `Ticket-ref: tickets/NNNN-...` to reference a ticket without closing it, or `Ticket: none` for a PR that closes nothing.
- **Rebase at every gate, not just before merge.** Rebase onto current `origin/main` (then push `--force-with-lease` and wait for CI) before each hand-off: opening the merge request, invoking `/verify`, and merging. Each gate validates the *combination* branch ⊕ base — a verdict on a stale base is partially void, and under parallel sessions staleness accrues continuously (2026-06-04: a PR opened current went 17 commits stale in 18 minutes and burned a full `/verify` round on the mergeability circuit-breaker). This also prevents "Base branch was modified" failures mid-merge and keeps history linear.
- **After an APPROVED `/verify`, sync before merging.** `/verify` may commit and push fixes from its own review worktree, leaving your local branch behind `origin`. Run `git fetch origin && git merge --ff-only origin/<branch>` before you rebase/merge — otherwise a rebase + `--force-with-lease` silently drops the verify fix.
- **Merge-bounce recovery.** `erg-pr-merge` legitimately bounces in sequence; each bounce has a specific retry — do not blanket-fall back to `gh pr merge`:
  - *"close: no ticket found" on a retry* — the FIRST run already `erg close`d + archived + pushed the close commit (the script is **not** idempotent past that step). Do NOT re-run it and do NOT hand-close the ticket; the close commit is already on the branch, so finish with `gh pr merge <N> --merge` directly once CI is green.
  - *"must run from PR branch" after a fast-forward* — HEAD detached after `merge --ff-only`; `git checkout <branch>`, then retry.
- **Delete branches after merge.** All repos use `deleteBranchOnMerge: true` on GitHub, so the remote branch disappears automatically when a PR merges. Clean up stale local branches with:
  ```bash
  git fetch --prune
  for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
    git merge-base --is-ancestor "$b" origin/main && git branch -d "$b"
  done
  ```
  The old `git branch -vv | awk '/: gone]/'` pipeline silently no-ops under rtk output rewriting; the merge-probe loop keys on exit code, not parsed stdout, so it stays robust under any hook. The healthcheck's branch hygiene check flags stale locals; this is how to resolve them. Do not use `git branch -D` on a branch whose PR you have not verified is merged.
- **Don't gitignore handoff artifacts.** Generated files that a downstream workpackage consumes (figures, tables, macros `\input`ed by the manuscript) are durable state — commit them. Caches, LaTeX aux files, and the final rendered PDF are regenerable — gitignore.
