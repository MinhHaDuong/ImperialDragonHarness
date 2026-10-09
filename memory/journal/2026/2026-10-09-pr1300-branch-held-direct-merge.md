# PR 1300: PR branch held by another worktree, direct forge merge

Date: 2026-10-09. Ticket 0375, PR 1300 (rules consolidation trial).

- The PR branch `t0375-trial` was checked out in worktree
  `.claude/worktrees/agent-a737a9f1dde31f044`, left by an earlier agent. The new
  session worked on its own branch `worktree-t0375-970241`, reset to
  `origin/t0375-trial`, and pushed with `HEAD:t0375-trial`.
- `erg-pr-merge -C <worktree> 1300` refused: "must run from PR branch
  't0375-trial'". The isolation guard refused git commands targeting the other
  worktree, and compound shell commands containing git.
- Per `/merge`'s fallback, the PR was merged with `gh pr merge --merge --auto
  --match-head-commit`. The body carried `Ticket-ref:` only, so no close claim was
  at stake. It merged at 12:36Z with all checks green.
- Cross-family review via `codex exec -s read-only -m gpt-6-luna` took three
  passes: 7 minor findings, then 1 stale-index finding, then APPROVE. The
  attribution validator rejected bare model ids and accepted
  `anthropic/…` and `openai/…` forms.
