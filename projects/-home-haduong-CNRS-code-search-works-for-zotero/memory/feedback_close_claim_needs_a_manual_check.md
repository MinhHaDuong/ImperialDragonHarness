---
name: feedback-close-claim-needs-a-manual-check
description: "erg-pr-merge cannot run when the PR branch sits in another session's worktree; merge server-side, then close the claimed tickets by hand and verify"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 43bfbf20-0cb6-46b3-bcbd-d03a2e7e6911
  modified: 2026-08-29T14:13:59.644Z
---

`erg-pr-merge` must run from the PR head branch. In this repo several PR
branches are checked out in *other* sessions' worktrees, and the worktree
isolation guard correctly refuses `git -C` into them. So in a batched merge wave
the only route is `gh pr merge <N> --merge` — which merges the code and
**silently skips the ticket close** the PR's `**Ticket:**` line claimed.

Nothing flags this. The PR shows MERGED, `erg check` passes, `make check` is
green, and the ticket just stays open in the queue.

**Why:** happened on PRs #43 (ticket 0017) and #44 (ticket 0051), 2026-08-29.
Caught only by checking by hand afterwards. A sweep over 40 merged PRs found 3
close claims and 0 unhonoured *after* the repair — run that sweep reporting
three counts (PRs seen, claims parsed, unhonoured), because zero claims parsed
means the parser broke, not that the repo is clean.

**How to apply:** after any `gh pr merge` of a PR whose body carries a
`**Ticket:**` (not `Ticket-ref:`) line, close the ticket with the manual recipe
from `tickets/AGENTS.md` — and mind its ordering trap: `git add -u tickets/`
runs **before** the `git mv` to `closed/`, or the rename carries the pre-edit
blob and drops the `Closed:` header. Two related facts: an `.erg` ticket can
carry **several** `Blocked-by:` lines, so `grep -m1` under-reports the blocked
graph; and closing a ticket with an unmet criterion is allowed (a `**Ticket:**`
line closes unconditionally) but the residue belongs in the close reason, not
quietly ticked. See [[feedback_guard_the_silent_failure_first]].

**Better recipe, 2026-09-02 (PR #227, ticket 0597): close it *before* merging,
by pushing to the head ref.** The manual after-the-fact close above is a repair;
this avoids the hole entirely. The blocker is only that `erg-pr-merge` needs the
branch *checked out*, and a second `git worktree add` refuses a branch another
worktree holds. But nothing needs the branch **name** — build the close commit in
a detached worktree at the PR head and push it to the ref:

```bash
git worktree add --detach /tmp/scratch origin/<pr-branch>   # from an allowed cwd
cd /tmp/scratch
./tickets/erg close <ID> "<reason>" tickets/
git add -u tickets/          # BEFORE the archive move — the ordering trap above
./tickets/erg archive <ID> tickets/
git add tickets/             # stages the rename
git commit …                 # verify: the staged diff shows +Closed:, not a bare rename
git push origin HEAD:<pr-branch>
gh pr merge <N> --merge
```

The close then rides the PR as a normal commit, the merge is ordinary, and there
is nothing left to sweep for afterwards. The abandoned lane worktree that holds
the branch name goes stale, which is harmless. Verify before pushing: a
100%-rename / 0-insertion commit is the tell that the `Closed:` header was
dropped.
