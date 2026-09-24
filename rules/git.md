<!-- last-reviewed: 2026-09-24 -->
# Git Discipline

Resident in every session. Rules only; the incidents behind them live in
memory notes and tickets.

## Branch and commit

- **Always work on a branch.** Main is read-only. Everything (code, docs, tickets, STATE, memory, config) lands via branch + PR; the forge gate is closed, there is no direct-push path. Sole exception: manuscript prose in paper repos — § Prose workpackages below.
- **One change per commit.** The message explains *why this change and not another*: alternatives considered, local design choices made. Merge commits carry the strategic level — architecture decisions, cross-file impacts, residual debt.
- **Git is the project's long-term memory.** Top-level files reflect *now*; history lives in `git log`.
- **Worktrees are throwaway, branches hold durable state.** Never `rm -rf` a worktree the runtime created; `git worktree prune` after deleting the branch.

## Commands that destroy silently

Family rule: **a git command that printed nothing has not necessarily done nothing.** Before reaching for one of these, ask what it writes that you did not name.

- **Never round-trip through `git stash` in a shared checkout.** The stack is repo-global: on a clean tree `stash` saves nothing and the `pop` grabs someone else's. Use a throwaway `git worktree add` or a WIP commit.
- **`git checkout <ref> -- <path>` is a write, not a read.** It overwrites index and tree at that path with no reflog, and arrives disguised as measurement ("restore it just to compare"). To read another version: `git show <ref>:<path>`; to build one: a throwaway worktree.

## Merging

- **Merge through `/merge`.** It reads merge settings at merge time (they drift), carries the close-claim syntax, syncs after an APPROVED `/gaze`, and holds the recoveries: a denied force-push, a direct forge merge that skipped a `**Ticket:**` claim (§ Dropped close-claim sweep), a multi-PR wave whose union must be verified and a conflict in a *generated* file, which is regenerated, never hand-merged (`/merge` § Merge conflict recovery). One ticket per PR unless they genuinely land together.
- **Rebase at every gate, not just before merge.** A gate validates branch ⊕ base, so a verdict on a stale base is partly void. Rebase onto current `origin/main`, force-push with lease, wait for CI — before opening the MR, before `/gaze`, before merging.
- **Anchor branch-mutating git after a fork returns.** The shell cwd may sit in another worktree: before the first `switch`/`checkout`/`merge`/`rebase`/`commit`/`push`/`reset` of that turn, check `git rev-parse --show-toplevel` or use `git -C <path>`.
- **Propose `/roar` after a merge lands** — propose, don't auto-run.

## Branch cleanup

- **Delete branches after merge, and only after an ancestry probe.** The
  probe-guarded sweep, local and remote, is `/roar` step 10 — run it there
  rather than improvising a loop. Never `git branch -D` a branch whose merge
  you have not verified.

## Reading state you will act on

- **Never read a SHA, a count, or a tip from output a proxy may rewrite.** The `rtk` hook compacts for a reader, not a parser: counts came back zero, `git log` dropped merge commits, and past ~2 kB it truncates head-first, so a test runner's verdict goes first. Use plumbing that answers in exit codes and single values (`git rev-parse`, `git rev-list --count A..B`, `git merge-base --is-ancestor`). What it spares moves between versions: ask `rtk hook check <cmd>`. Escape hatches: `RTK_DISABLED=1`, `/usr/bin/git -C <worktree> …` (also the remedy when the rewrite makes the isolation guard fail closed); `~/.local/share/rtk/tee/` keeps unfiltered output.
- **Verify a forge mutation by reading it back.** `gh pr edit --body` can exit non-zero behind a harmless-looking deprecation warning, body unchanged; `gh api … -X PATCH --input -` fed by `jq -n --rawfile body <file>` works. **An all-clear indistinguishable from "I could not look" is not a check.**
- **Local main syncs by ref, never by assumption:** `scripts/sync-local-main.sh`, run at session start and after `/merge`. Never `git branch -f main`, never stash a dirty file to force a sync.

## Repo layout

- **Don't gitignore handoff artifacts.** Generated files a downstream workpackage consumes (figures, tables, `\input` macros) are durable — commit them; caches, aux files and the final PDF are regenerable — gitignore. Sources and bibliography staging: [edm.md](./edm.md), Zotero is their system of record.
- **Prose workpackages are edited in place; the author edits only in their own checkout.** In paper repos, worktree + branch + PR covers code and data; manuscript prose is co-edited in short interactive turns in the author's checkout, committed at session end or milestones, reviewed as the PDF and `latexdiff` between tags. Autonomous prose passes produce *reports*; an autonomous manuscript change goes through a PR, never concurrently with interactive editing of that file. Agents carry the sync, never the author: pull before editing a file the author may have touched; agent work reaches them only through `main` (`scripts/sync-local-main.sh`); show unmerged work as a diff, a build or a PR link, never "open the worktree". The harness repo keeps its no-exceptions gate.
- **Name workpackage directories in plain language** (`marches-carbone/`, not `p1/`); program codes stay in tickets.
