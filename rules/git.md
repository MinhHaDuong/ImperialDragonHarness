<!-- last-reviewed: 2026-11-01 -->
# Git Discipline

Resident. Rules only; incidents live in memory and tickets.

## Branch and commit

- **Agents work on a branch.** Main is read-only to them: everything (code, docs, tickets, memory, config) lands via a merge request, except below.
- **The author edits in the primary checkout.** Agents sync it, assist the author's prose edits and commit or land them on request, a trivial one straight to main only with the author's leave: `ALLOW_MAIN_COMMIT=1 git -c idh.mainGuard=warn commit`.
- **One change per commit.** The message explains *why this change and not another*: alternatives considered, local design choices made. Merge commits carry the strategic level — architecture decisions, cross-file impacts, residual debt.
- **Git is the project's long-term memory.** Top-level files reflect *now*; history lives in `git log`.
- **Worktrees are throwaway, branches hold durable state.** Never `rm -rf` a worktree the runtime created; `git worktree prune` after deleting the branch.

## Commands that destroy silently

- **A git command that printed nothing may still have written.** Before running one, check what it changes beyond the paths you gave it.
- **Never round-trip through `git stash` in a shared checkout.** The stack is repo-global: on a clean tree `stash` saves nothing and the `pop` grabs someone else's. Use a throwaway `git worktree add` or a WIP commit.
- **`git checkout <ref> -- <path>` is a write, not a read.** It overwrites index and tree at that path with no reflog, and arrives disguised as measurement ("restore it just to compare"). To read another version: `git show <ref>:<path>`; to build one: a throwaway worktree.

## Merging

- **Merge by the merge skill.** One ticket per merge request unless they land together.
- **Rebase before every gate.** A verdict on a stale base is partly void. Rebase onto `origin/main`.
- **Anchor branch-mutating git after a fork returns.** The shell cwd may sit in another worktree: before the first `switch`/`checkout`/`merge`/`rebase`/`commit`/`push`/`reset` of that turn, check `git rev-parse --show-toplevel` or use `git -C <path>`.
- **Remind the user of a merge left without its `/roar`.** Once, before you hand back.
- **Roar's step 10 cleans only its task's branches and worktrees**; the rest is lair/molt's.

## Reading state you will act on

- **Never read a SHA, a count, or a tip from output a proxy may rewrite.** The `rtk` hook compacts for a reader, not a parser: it can rewrite counts, drop commits and truncate long output head-first. Use plumbing that answers in exit codes and single values (`git rev-parse`, `git rev-list --count A..B`, `git merge-base --is-ancestor`). Escape hatches: [RTK.md](../RTK.md).
- **Verify a forge mutation by reading it back, in the same command**. Exit codes and warnings do not tell you whether it landed. **An all-clear indistinguishable from "I could not look" is not a check.**
- **Local main syncs by ref, never by assumption:** `scripts/sync-local-main.sh`, run at session start and after a merge. Never `git branch -f main`, never stash a dirty file to force a sync.
