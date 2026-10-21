# Gaze — scratch cleanup and containment

Loaded from `skills/gaze/SKILL.md`; runs on every exit path.

## Review scratch cleanup

On every exit path (REVIEWED, FINDINGS, ESCALATE, circuit-breaker abort), after the review panel has consumed its artifacts, remove this
run's review scratch before removing the worktree.
The `/review-pr` run leaves the panel for this step. Do not run
this while perspective agents are still writing: cancel or wait for them first.
If the review worktree was never created, there is nothing to clean up. The
exit preflight must pass after scratch removal: if it reports other WIP, leave
the review worktree registered and surface those file names as ESCALATE to the
caller. Never force-remove a tree with real uncommitted files. A failed
preflight or normal worktree removal is a cleanup failure, not a successful
terminal result.

```bash
review_tree="$primary_root/.claude/worktrees/review-<pr-number>"
if [ -d "$review_tree" ]; then
    # Read verdicts before deleting panel files. Citation or ancestry uncertainty
    # keeps both the candidate .tmp and its review evidence in place.
    if [ -e "$review_tree/.tmp" ] || [ -L "$review_tree/.tmp" ]; then
        python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" removal \
            "$primary_root" "$review_tree" --branch "$PR_BRANCH" || exit 1
    fi
    tracked_panel=$(git -C "$review_tree" ls-files -- ".panel/<pr-number>") || exit 2
    tracked_base=$(git -C "$review_tree" ls-files -- build/panel-head) || exit 2
    [ -n "$tracked_panel" ] || rm -rf -- "$review_tree/.panel/<pr-number>"
    if [ ! -L "$review_tree/build" ] && [ -z "$tracked_base" ]; then
        rm -rf -- "$review_tree/build/panel-head"
    fi
    rmdir -- "$review_tree/.panel" 2>/dev/null || true
    # Detached review trees without provable branch ancestry retain .tmp.
    if ! "$IDH_ROOT/scripts/worktree-exit-preflight.sh" --removal --branch "$PR_BRANCH" "$review_tree"; then
        echo "/gaze cleanup blocked: real WIP remains in $review_tree" >&2
        exit 1
    fi
    git -C "$primary_root" worktree remove "$review_tree" || exit 1
fi
```


## Containment postcondition

On **every** exit path (REVIEWED, FINDINGS, ESCALATE, circuit-breaker abort), after removing the review worktree and before returning control to
the caller — the caller must see this report before any merge step:

```bash
git rev-parse --show-toplevel               # FIRST: confirm cwd is the session
                                            # worktree — the forks just returned,
                                            # so a drifted cwd would make the two
                                            # reads below report a foreign tree's
                                            # state (rules/git.md § anchor)
git status --porcelain                      # invoking session worktree
git branch --show-current                   # must equal the branch on entry
git -C <primary-repo-root> status --porcelain
```

- **Foreign files** (anything this run did not deliberately create —
  especially stray `tickets/*.erg`) → remove or restore them, and flag the
  contamination in the result comment. Do not leave them for a later
  `git add` to sweep.
- **Unexpected branch** → switch back to the entry branch and flag it. Never
  end the skill with the session worktree on a different branch than it was
  on at phase 1. This runs right after the review forks return, so the shell
  cwd may sit in a foreign worktree: confirm the tree first
  (`git rev-parse --show-toplevel` should equal the session worktree), then
  anchor the corrective switch — `git -C <session-worktree> switch <entry-branch>`,
  not a bare `git switch` against an assumed cwd (rules/git.md § anchor across
  a forked-skill boundary).
- Anything that cannot be restored cleanly → downgrade the result to
  ESCALATE; a contaminated workspace must not feed a merge.
