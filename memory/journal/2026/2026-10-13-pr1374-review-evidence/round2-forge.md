# PR 1374 review round 2

Forge review: PRR_kwDORsAV3c8AAAABR1hh2A
Reviewed commit: 86296e73c9fd82536e0fecbab8c27a040431a405
Submitted: 2026-10-12T14:09:15Z

## /review-pr round 2 — PR #1374 (anchor 86296e73)

Panel: the four round-1 seats that returned comment (correctness, consistency, red team, doc propagation) re-run; scope not run. Width: 7 files / 428 lines, `scripts/**` and `skills/**` matched. All seats same-family (Anthropic: opus correctness and red team, sonnet consistency and doc propagation); none independent. Gate: `make check` 1558 passed, 4 skipped (full gate).

Round-1 items all verified fixed by running them: step 10 ROAR_DIR preamble, tip==base-tip branches kept, `lstrip=2/3` ref names, `--ticket` without value exits 2, probe error gives could-not-look, mutants moved out of the tracked tree.

### Should fix (red team; dissent: it requests changes)
1. **Remote delete has no lease** (red team F1). Between `git fetch --prune` and `git push origin --delete "$b"`, a colleague's new push to a merged branch is deleted on the forge, where it may be the only copy. Use `git push --force-with-lease="refs/heads/$b:$(git rev-parse refs/remotes/origin/$b)" origin ":refs/heads/$b"`. The window is small; the other seats did not raise it. Author decides.

### Minor
- verifiable: a remote branch sharing a name with a remote tag reports `FAILED to delete remote v1`, exit 1 (red team repro); the fully qualified refspec above fixes it.
- verifiable: a local branch named `-D` (via update-ref) gives `FAILED to delete local -D`; `git branch -D -- "$b"` fixes it. Safe, only a false finding.
- consider: a fast-forward-merged branch at the base tip is reported "unmerged kept" (correctness); label it "at-base kept".
- consider: `ROAR_DIR="${ROAR_DIR:-...}"` trusts an inherited env var; SKILL.md always sets the same value (correctness).
- consider: SKILL.md 9a says to re-run `close-and-clean.sh --phase before-exit` bare; say "re-run the step-7 command" (doc propagation).
- consider: `scripts/worktree-exit-preflight.sh:11` is 105 columns; rewrap (consistency, doc propagation).
- consider: ticket 1089 is unrelated to roar and the 1084 log calls it a "follow-up"; split it out or relabel; align the Minh Ha-Duong / Minh-Ha-Duong spelling (consistency).
- consider: the remote side has no worktree guard; a merged origin copy of a branch checked out elsewhere is deleted (local survives). State it in SKILL.md (red team).
- consider: the PR body must keep a non-closing reference to 1084; its last exit criterion is open.
- nofollow: older-ancestor branches still swept (hold no unique commits); journal line numbers; env overrides as trust boundary.

### Verdict roster
- correctness: approve
- consistency: comment
- red team: request-changes (item 1)
- doc propagation: approve
- scope: not run

Synthesis verdict: comment. Item 1 is recommended before merge but is a narrow race, not a regression from the inherited recipe. dissent: red team requests changes on item 1; the other three seats do not. All same-family, no cross-family check done.
