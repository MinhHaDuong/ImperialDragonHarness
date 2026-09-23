<!-- last-reviewed: 2026-09-10 -->
# Git Discipline

Every line here is resident in every session (`rules/README.md`). Rules only:
the incidents that established them live in memory notes, cited inline.

## Branch and commit

- **Always work on a branch.** Main is read-only. Everything (code, docs, tickets, STATE, memory, config) lands via branch + PR; the forge gate is closed, there is no direct-push path. See `rules/workflow.md` § Worktree paths. Sole exception: manuscript prose in paper repos — § Prose workpackages below.
- **One change per commit.** The message explains *why this change and not another*: alternatives considered, local design choices made. Merge commits carry the strategic level — architecture decisions, cross-file impacts, residual debt.
- **Git is the project's long-term memory.** Top-level files reflect *now*; history lives in `git log`.
- **Worktree isolation is automatic** — the SessionStart hook enforces it. Worktrees are throwaway, branches hold durable state. Never `rm -rf` a worktree created by the agent runtime; `git worktree prune` after deleting the branch.

## Commands that destroy silently

Family rule: **a git command that printed nothing has not necessarily done nothing.** Before reaching for one of these, ask what it writes that you did not name.

- **Never round-trip through `git stash` in a shared checkout.** The stash stack is repo-global, shared by every worktree and session: on a clean tree `stash` saves nothing, so the `pop` grabs someone else's. Need a clean baseline? A throwaway `git worktree add`, or a WIP commit. If you must: `git stash push -m <name>`, pop only after `git stash list` shows your entry on top, `drop` it on conflict after resolving.
- **`git checkout <ref> -- <path>` overwrites the index, not just the working tree.** It is a write, not a read, and it destroys staged work at that path with no reflog to recover it. It arrives disguised as measurement — "let me restore the file just to compare" — which is exactly when uncommitted work is in flight. To *read* another version: `git show <ref>:<path>`. To *build* one: a throwaway worktree. To compare in place: commit first (`reset --soft` undoes it).

## Merging

- **Read merge settings at merge time.** They drift, and branch protection can reject a method the forge API advertises. `/merge` § Before merging covers this repo's hardcoded `--merge` and squash ancestry.
- **Create a merge request** for each ticket, with a close-claim line in the PR body — full syntax and semantics are documented in `/merge` § Ticket lines in the PR body. One ticket per PR is the review hygiene; list several only when they genuinely land together.
- **Rebase at every gate, not just before merge.** Each gate validates the *combination* branch ⊕ base, so a verdict on a stale base is partially void, and under parallel sessions staleness accrues by the minute. Rebase onto current `origin/main`, force-push with lease, wait for CI — before opening the MR, before `/gaze` (its own invariant restates this), before merging.
- **Force-push denied on a pushed branch → merge as-is.** A rebase can strand the ticket-close commit locally. Use `/merge` § When the script bounces for recovery.
- **After an APPROVED `/gaze`, sync before merging** — `/gaze` may have pushed fixes from its own review worktree since you last fetched; the sync recipe is `/merge` § Before merging, not a manual step here.
- **A direct forge merge silently skips `**Ticket:**` close claims.** When another session's worktree makes the PR branch unreachable to `erg-pr-merge`, verify the claimed ticket reached `tickets/closed/` with a `Closed:` header. After a wave, run `/merge` § Dropped close-claim sweep; check PR, claim and unhonoured counts, then repair drops via § Manual chore-close.
- **Multi-PR wave on one file: verify the union survived, don't trust a clean exit.** A stale `origin/main` ref produces a clean-looking auto-merge that silently drops a sibling's non-conflicting addition. Recovery procedure: `/merge` § Merge conflict recovery.
- **Conflict inside a *generated* file: regenerate, don't hand-merge.** A generated file carries no marker of which input produced it, so a stale-input regeneration can silently revert another branch's data fix while looking clean. Recovery procedure: `/merge` § Merge conflict recovery.
- **Anchor branch-mutating git across a forked-skill boundary.** After a forked sub-skill or an isolated agent returns, the shell cwd may sit in a different worktree than the conversation assumes. Before the FIRST `switch`/`checkout`/`merge`/`rebase`/`commit`/`push`/`reset` of that turn, confirm with `git rev-parse --show-toplevel` or anchor with `git -C <path>`. Post-fork only: in linear flow the shell self-resets after every command.
- **Propose `/roar` after a merge lands** — the wrap-up saves lessons, refreshes state, cleans branches. Propose, don't auto-run: the author decides.

## Branch cleanup

- **Delete branches after merge, and only after an ancestry probe.** Whether the
  forge deletes the remote branch itself is a per-repo setting: check it, don't
  assume, and sweep the remote side too where it is off. The sweep — local and
  remote, probe-guarded — is `/roar` step 10; run it there rather than
  improvising a loop, since each of its guards exists for a branch someone lost
  (memory `reference_branch_cleanup_incidents`). Outside that
  probe, never `git branch -D` a branch whose merge you have not verified.

## Reading state you will act on

- **Never read a SHA, a count, or a tip from a bare command whose output a proxy may rewrite.** The `rtk` hook compacts for a reader, not a parser: counts came back zero and `git log` dropped merge commits including the range's tip. Use plumbing that answers in exit codes and single values: `git rev-parse`, `git rev-list --count A..B`, `git merge-base --is-ancestor`. What the hook spares moves between rtk versions, so ask `rtk hook check <cmd>` rather than recall a shape; escape hatches in `workflow.md` § Diagnosis discipline.
- **A launcher in front of `git` can make the isolation guard fail closed.** rtk rewrites bare `git X` into `rtk git X`, and a guard reading only a plain command line cannot then prove the call stays in the worktree; piping does not dodge it, the objection being to the rewrite, not the output framing. Seen in one repo's worktree session, not reproduced in another's hours later — a refusal a session *can* meet, not one it always meets. Remedy: `/usr/bin/git -C <worktree> …`, which dodges the rewrite and names the tree.
- **Verify a forge mutation by reading it back.** `gh pr edit --body` has been seen to fail the body mutation while emitting a Projects-classic deprecation warning that reads like a harmless aside — exit non-zero, body unchanged. Workaround: `jq -n --rawfile body <file> '{body: $body}' | gh api repos/<owner>/<repo>/pulls/<N> -X PATCH --input -` (not `-f body=@file`, whose `@` special-casing sends the literal path). The general form is the trap this file keeps meeting: **an all-clear indistinguishable from "I could not look" is not a check.**
- **Local main syncs eagerly, by ref — never by assumption.** The primary checkout is shared state and may sit on any branch, so a bare `merge --ff-only` there advances whatever is checked out. Use `scripts/sync-local-main.sh`: it fast-forwards the default branch by ref, ff-merges in the one worktree that has it out, and reports instead of touching diverged state. It runs at session start and after `/merge`. Never `git branch -f main`, never stash a dirty file to force a sync.

## Repo layout

- **Don't gitignore handoff artifacts.** Generated files a downstream workpackage consumes (figures, tables, macros the manuscript `\input`s) are durable state — commit them. Caches, aux files and the final rendered PDF are regenerable — gitignore. Source documents and bibliography staging follow a separate discipline, see [edm.md](./edm.md): Zotero, not git, is their system of record.
- **Prose workpackages are edited in place, not behind a worktree.** In paper repos, worktree + branch + PR applies to code and data (`analysis/`, scripts, pipelines) — agent-produced, test-verifiable, reviewed as a diff. Manuscript prose is co-edited with the author in short interactive turns, and isolation cuts him off from the text (decided 2026-07-06). Edit manuscripts directly in the author's checkout; commit at session end or milestones. The review interface for prose is the recompiled PDF and `latexdiff` between tags, not a PR diff. Autonomous passes on prose produce *reports* (referee panels, source registers, saturation notes), never direct manuscript edits; an autonomous change to a manuscript goes through branch + PR for the author to arbitrate, and the two modes never run concurrently on the same file. Collision protection is lane separation, not git isolation. Paper repos only — the harness repo keeps its no-exceptions gate.
- **Name workpackage directories in plain language** (`marches-carbone/`, not `p1/`). Program codes stay in tickets and conception notes as cross-references (decided 2026-07-06).
