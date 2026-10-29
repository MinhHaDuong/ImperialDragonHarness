# Gaze — scratch cleanup and containment

Loaded from `skills/gaze/SKILL.md`; runs on every exit path.

## Review scratch cleanup

On every exit path (REVIEWED, FINDINGS, ESCALATE, circuit-breaker abort), after the review panel has consumed its artifacts, remove this
run's review scratch before removing the worktree.
The panel (`references/panel.md`) leaves its artifacts for this step. Do not run
this while perspective agents are still writing: cancel or wait for them first.
Do not gitignore `.panel/` in adopter repos: an ignore rule hides a missed
cleanup from the worktree gates.
If the review worktree was never created, there is nothing to clean up. The
exit preflight must pass after scratch removal: if it reports other WIP, leave
the review worktree registered and return ESCALATE naming those files. Never force-remove a tree with real uncommitted files. A failed
preflight or normal worktree removal is a cleanup failure, not a successful
terminal result.

`"$IDH_ROOT/scripts/gaze_close.py"` runs these steps in order (its source is the
contract that `tests/test_review_panel_cleanup_contract.py` pins): the
`.tmp` guard (`worktree-tmp-guard.py removal`) before any deletion; removal of
`.panel/<pr-number>` and `build/panel-head` when untracked;
`worktree-exit-preflight.sh --removal --branch <branch>`; plain
`git worktree remove`, never `--force`. A blocked step exits 1 and leaves the
review worktree registered; the script records an ESCALATE answer on notes and
posts its pointer: return ESCALATE naming the files. Attribution was appended
before cleanup, so the review is recorded either way, and the ESCALATE answer
carries the generated `seat:` lines, read before the panel was removed.

## Containment postcondition

On **every** exit path (REVIEWED, FINDINGS, ESCALATE, circuit-breaker abort), after removing the review worktree and before returning; the report goes
in the result:

The script reads, and prints as `containment: ...`: the toplevel of the session
tree `gaze_setup.py` recorded at entry (not cwd: a runtime may have moved the shell
between setup and close, and a drifted cwd would report a foreign tree's state;
an entry state without it reads the cwd), `git status --porcelain` of the
invoking session worktree, its branch (compared to `--entry-branch`), and the
primary checkout's status; lines already present at entry (recorded by `gaze_setup.py`) are the caller's own work, not findings. Any finding exits 4 (the result is still recorded
with the report); the repairs below stay with gaze.

- **Foreign files** (anything this run did not deliberately create —
  especially stray `tickets/*.erg`) → remove or restore them, and flag the
  contamination in the result. Do not leave them for a later
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
  ESCALATE.
