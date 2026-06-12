---
name: feedback-ticket-housekeeping-on-main
description: "all main-targeted commits must go through a PR — branch protection rejects direct pushes (GH006), including tickets and STATE.md refreshes"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 61156091-0161-4b75-a070-0798f4d69f07
---

**Updated 2026-05-28 (raid 0358):** branch protection on `main` requires **4** status checks: `changes`, `lint`, `tests`, `build` (`build` = the docs-build workflow's job, added by ticket 0365). `enforce_admins=true` so admins do NOT bypass; auto-mode classifier blocks attempts to weaken it without explicit user authorization. **Any** direct push to main fails with `GH006: Protected branch update failed for refs/heads/main`. This includes:
- Ticket lifecycle commits with `tickets:` prefix
- STATE.md refreshes (`STATE:` prefix)
- Any other housekeeping that previously bypassed PR

**Workflow:**
1. Create a branch (`claude/ticket-<id>-<slug>` or `claude/rename-<...>`).
2. Push the branch.
3. Open a PR with `gh pr create`. Include `**Ticket:** tickets/NNNN-...erg` in the body if the PR opens or closes a ticket (so erg-pr-merge auto-closes on merge).
4. CI runs all 4 required checks. `build` runs full (~1m16s) even on chore PRs because the `changes`-job chore filter is broken (see ticket 0377) — wasted CI minutes only, not a gate failure.
5. Merge with `gh pr merge <N> --merge --delete-branch --auto` (NOT `--squash` — repo rejects squash, error: "Squash merges are not allowed on this repository"). `--auto` is the zero-friction path: enable it right after creating the PR and the merge fires the moment the 4 checks finish. Do NOT try `--admin` — the auto-mode classifier blocks it unless the user explicitly authorized that specific PR's merge. For chore PRs (tickets/STATE/docs only), checks finish in ~30 s because the `chore` path filter short-circuits the heavy steps.
6. The `~/.claude/skills/merge/erg-pr-merge` script pushes a ticket-close commit before the GH merge (good), then tries squash and fails (do the merge manually after the close commit is up). Note: it also requires the local branch name to match the PR head branch — `git branch -m <pr-head-name>` if it doesn't.

**Why:** Confirmed empirically 2026-05-28 in the 0358 raid (PRs #638, #639, #644). The 2026-05-27 conference temporarily disabled required-checks (per ticket 0358's stated cause); 0358 re-enabled them + added the new `build` check.

**How to apply:**
- Small ticket lifecycle commits (close/open/edit) → branch + PR + auto-merge, even if the change is 2 lines.
- For batched ticket changes (e.g. close 0179 + open 0180), bundle in one commit on the branch.
- Format commit: `tickets: <verb> <ticket-id> (<short reason>), <verb> <ticket-id> (<short reason>)`.
- PR title: `tickets: <one-line summary>`.
- Does NOT apply to ticket *implementation* — that always went on a branch + PR (no change there).

**Note:** If a future commit succeeds in pushing directly to main, branch protection rules may have been relaxed — re-check before assuming.
