<!-- last-reviewed: 2026-09-24 -->
# Git Discipline

Resident in every session. Rules only; the incidents behind them live in
memory notes and tickets.

## Branch and commit

- **Agents work on a branch.** Main is read-only to them: everything (code, docs, tickets, STATE, memory, config) lands via branch + merge request, except below.
- **The author edits in the primary checkout.** Agents sync it, assist the author's prose edits there ([prose/workpackages.md](./prose/workpackages.md)) and commit or land them on request; a trivial one the author may commit to main with `git -c idh.mainGuard=warn` (journaled; author only).
- **One change per commit.** The message explains *why this change and not another*: alternatives considered, local design choices made. Merge commits carry the strategic level — architecture decisions, cross-file impacts, residual debt.
- **Git is the project's long-term memory.** Top-level files reflect *now*; history lives in `git log`.
- **Worktrees are throwaway, branches hold durable state.** Never `rm -rf` a worktree the runtime created; `git worktree prune` after deleting the branch.

## Commands that destroy silently

Family rule: **a git command that printed nothing has not necessarily done nothing.** Before reaching for one of these, ask what it writes that you did not name.

- **Never round-trip through `git stash` in a shared checkout.** The stack is repo-global: on a clean tree `stash` saves nothing and the `pop` grabs someone else's. Use a throwaway `git worktree add` or a WIP commit.
- **`git checkout <ref> -- <path>` is a write, not a read.** It overwrites index and tree at that path with no reflog, and arrives disguised as measurement ("restore it just to compare"). To read another version: `git show <ref>:<path>`; to build one: a throwaway worktree.

## Merging

- **Merge by the merge skill.** It reads merge settings at merge time (they drift), carries the close-claim syntax, syncs after gaze, checks the gate record and holds the recoveries (merge § Merge conflict recovery). One ticket per merge request unless they land together.
- **Rebase before every gate.** A verdict on a stale base is partly void. Rebase onto `origin/main`, force-push with lease, wait for CI — before the MR, before gaze, before the round-1 verify-gate; a later rebase is gated by the tier of what it changes (merge § Gating tiers).
- **Anchor branch-mutating git after a fork returns.** The shell cwd may sit in another worktree: before the first `switch`/`checkout`/`merge`/`rebase`/`commit`/`push`/`reset` of that turn, check `git rev-parse --show-toplevel` or use `git -C <path>`.
- **Remind the user of a merge left without its `/roar`.** Once, before you hand back.

## Branch cleanup

- **Roar's step 10 cleans only the just-completed ticket and its merge**: branches
  named by its merged requests, at full approved head OIDs, ancestry checked,
  `-d` only, worktrees it owns. Others stay, even merged (lair/molt). Drift or
  unreadable evidence: retain and report, never force or compensate.

## Reading state you will act on

- **Never read a SHA, a count, or a tip from output a proxy may rewrite.** The `rtk` hook compacts for a reader, not a parser: it can rewrite counts, drop commits and truncate long output head-first. Use plumbing that answers in exit codes and single values (`git rev-parse`, `git rev-list --count A..B`, `git merge-base --is-ancestor`). What it spares moves between versions: ask `rtk hook check <cmd>`. Escape hatches: `RTK_DISABLED=1`, `/usr/bin/git -C <worktree> …`; `~/.local/share/rtk/tee/` keeps unfiltered output.
- **Verify a forge mutation by reading it back, in the same command**. Exit codes and warnings do not tell you whether it landed. **An all-clear indistinguishable from "I could not look" is not a check.**
- **Local main syncs by ref, never by assumption:** `scripts/sync-local-main.sh`, run at session start and after a merge. Never `git branch -f main`, never stash a dirty file to force a sync.

## Repo layout

Paper-repo rules (handoff artifacts, prose workpackages, workpackage
naming) live in [prose/workpackages.md](./prose/workpackages.md) — scoped,
loaded on prose-file touch. Sources and bibliography staging:
[zotero.md](./zotero.md), Zotero is their system of record.
