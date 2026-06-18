---
name: feedback_cross_pr_ticket_id_collision
description: Per-branch erg check can't see a ticket-ID collision living across two open PRs; it only surfaces on main after the second merges. Scan open PRs before merging a ticket-filing PR.
metadata:
  type: feedback
---

The optimistic-ID-allocation trap (AGENTS.md, git-erg#282) bites *across open PRs*, not just the local checkout — and `erg check` cannot catch it. Each branch passes `erg check` independently because its IDs are unique *within that branch*; the duplicate only materializes on main after the second PR merges, by which point the first is already landed.

**Why:** allocation scans only the local checkout, so two parallel sessions (or a stranded draft + an in-flight PR) hand out the same ID. The CI `validate-tickets` check runs per-branch and sees no conflict.

**How to apply:** before merging any ticket-filing PR (or committing a found/stranded ticket file), scan the IDs other open PRs add — `gh pr view <N> --json files` across `gh pr list` — not just `git ls-tree main tickets/`. On collision, keep the already-merged claimant and renumber the others to the next free IDs: `git mv` the file (the ID lives only in the filename), `erg check tickets/`, force-push, and update the PR title/body (`gh api -X PATCH`, since [[feedback_gh_pr_edit_broken_use_rest]]). Cost: 2026-06-18, merged a stranded `0257` (globalize-edm) that collided with open PRs #408 (0257/0258) and #410 (0258), forcing a three-way renumber to 0258/0259/0260 after the fact. Relates to [[feedback_cross_repo_tickets_live_at_destination]].
