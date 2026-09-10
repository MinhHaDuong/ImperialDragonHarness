---
name: merge
description: "Atomically close the linked ticket(s) and merge a PR. Must be run from the PR head branch. Works in git worktrees and on VMs. GitHub-only (requires the GitHub CLI)."
user-invocable: true
argument-hint: "[-C path] [pr-number]"
---

# Merge $ARGUMENTS

Run:
```bash
~/.claude/skills/merge/erg-pr-merge $ARGUMENTS
```

**Cross-repo prerequisite**: the script operates on the checkout it runs in,
with the PR branch checked out. Point it at a checkout in one of two ways:

- **`-C PATH` (preferred for agents)** — the script cds into `PATH` before any
  git/gh/erg call. The canonical agent invocation is the bare form
  `~/.claude/skills/merge/erg-pr-merge -C WORKTREE N`, which prefix-matches the
  standing allow rule `Bash(~/.claude/skills/merge/erg-pr-merge:*)` from any cwd.
  A `cd WORKTREE && …` prefix does **not** match that rule (the command text no
  longer starts with the script path), so it falls through to the stochastic
  auto-mode classifier — use `-C` instead of a `cd` prefix.
- **Implicit cwd** — with no `-C`, the script uses the current directory, so the
  caller must `cd <project-path> && git fetch origin` and check out the PR branch
  before the call.

`-C` with a missing or non-directory path fails loudly before any other work.

## Ticket lines in the PR body

The script reads close intent from the PR **body** only — never the title:

- `**Ticket:** tickets/NNNN-...` (bold or bare `Ticket:`) — a **close claim**:
  the named ticket is closed and archived on merge.
- `Ticket-ref: tickets/NNNN-...` — references a ticket **without closing it**
  (for annotating a deliberately-open ticket).
- `Ticket: none` — the PR closes nothing.
- With none of these lines and a `tickets/` dir present, the script errors.
- Title prefixes like `chore(0216):` are subject references — they **never**
  close anything.

Report stdout/stderr verbatim. If the script exits non-zero, stop and show the error.

A killed or failed `erg-pr-merge` run (non-zero exit after its rebase) can
leave the PR-branch worktree with a stale pre-rebase index: staged diffs that
appear to re-open closed tickets and revert prose. That is not WIP — run
`git reset --hard HEAD` in that worktree before any salvage or gc decision
(ticket 0249 incident, aedist PR #979).

Merge is queued via auto-merge; it lands when required checks pass (falls back to watch-then-merge where auto-merge is disabled). A **draft** PR (roar/raid sweeps file bootstrap PRs as draft) is marked ready automatically before merging — invoking `/merge` is explicit intent to merge.

## Before merging

Two prerequisites the caller checks before invoking this script. (Moved here
from `rules/git.md`, which is resident in every session: a recovery procedure
belongs with the command it recovers.)

- **Merge method drifts per repo.** This harness repo disables squash;
  `MERGE_FLAGS` above hardcodes `--merge`. A repo whose branch protection is
  squash-only rejects that flag — a method recorded in a note goes stale, so
  read the repo's actual merge settings rather than trusting a cached one.
  Trust the merge attempt over the flag: branch protection can bounce a method
  the forge API still advertises. On a squash-merged branch, `git cherry`
  shows `-` for every commit but `is-ancestor` is false — that ancestry check
  is `/roar`'s pre-check, and it is what confirms a squash-merge through the
  forge before a branch gets deleted.
- **After an APPROVED `/gaze`, sync before merging.** `/gaze` may have pushed
  fixes from its own review worktree since the caller last fetched:
  `git fetch origin && git merge --ff-only origin/<branch>` first, or a stale
  rebase silently drops the verify fix.

## Merge conflict recovery

- **Multi-PR wave on one file: verify the union survived, don't trust a clean
  exit.** Fetch before each sibling merge. A stale `origin/main` ref produces
  a clean-looking auto-merge that silently drops a sibling's non-conflicting
  addition — no conflict, exit 0, wrong content. "Auto-merging `<file>`" plus
  a clean exit is not proof the union survived: grep the merged file for
  every sibling's marker before committing. On a drop, don't hand-patch —
  restore the known-good base by writing `git show origin/main:<file>` to the
  path (never `git checkout <ref> -- <path>`, which overwrites the index),
  re-layer only this PR's change, re-verify.
- **Conflict inside a *generated* file: regenerate, don't hand-merge.**
  Hand-merging rows mixes one side's text with the other's measurements, so
  resolve the *source*. The subtler trap is the reverse: regenerating from a
  stale input reverts the other branch's data fix while producing a clean
  merge and a green suite, because a generated file carries no marker of
  which input produced it. Take `origin/main`'s copy as the base, regenerate
  to a scratch path, and grep the one value the other branch changed.
  Reproduces → commit. Reverts → your input is stale.

## When the script bounces

`erg-pr-merge` bounces in sequence, and each bounce has its own retry — never
blanket-fall back to a plain forge merge. (Moved here from `rules/git.md`,
which is resident in every session: a recovery procedure belongs with the
command it recovers.)

- **"close: no ticket found" on a retry.** The FIRST run already closed,
  archived and pushed the close commit — the script is *not* idempotent past
  that step. Do not re-run it and do not hand-close the ticket: the close
  commit is already on the branch, so finish with a direct forge merge once CI
  is green.
- **"must run from PR branch" after a fast-forward.** HEAD is detached after
  `merge --ff-only`: `git checkout <branch>`, then retry.
- **Force-push denied, branch already pushed.** Rebasing rewrites the branch's
  SHAs, local diverges from the remote, and the script's own ticket-close
  commit then lands on the local rewrite with its push rejected — leaving the
  ticket closed and archived locally but the close commit unpushed; a re-run
  fails "close: no ticket found". Recovery: check out the origin branch tip
  detached, `git cherry-pick <close-commit>`, fast-forward push, then merge
  directly (raid 234/235, PR #998).

## Manual chore-close — only when a PR merged without this script

First confirm no close commit rode the PR; if one did, the ticket is already
closed and there is nothing to do. `erg close <ID> <reason>` edits the ticket
file but does **not** stage its own edit, so `git add -u tickets/` BEFORE the
`git mv` to `closed/` and the commit — otherwise the commit carries the rename
with the pre-edit blob and silently drops the `Closed:` header (aedist PR #1008;
a 100%-rename, 0-insertion commit is the tell). A later "no ticket found"
bounce here means a review round already closed it — harmless, skip it.

## After the merge lands

The script itself polls for the merge to land and then runs
`~/.claude/scripts/sync-local-main.sh` on the base branch (rules/git.md
§ Local main syncs eagerly) — no manual sync step. Two outputs still need
action:

- "Merge queued but not yet landed" — the bounded poll ran out (slow CI).
  Confirm the PR reaches MERGED, then run `~/.claude/scripts/sync-local-main.sh`.
- "left untouched" in the sync report — dirty overlap or divergence where the
  base branch is checked out; report it to the caller rather than forcing.

Do not substitute a hand-rolled `merge --ff-only` on the primary checkout:
that advances whatever branch is checked out there.
