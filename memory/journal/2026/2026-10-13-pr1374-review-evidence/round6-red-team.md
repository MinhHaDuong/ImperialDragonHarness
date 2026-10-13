# PR 1374 red-team review, round 6 (author scope revision)

HEAD 3a5fcb313cb952694e5d24f1acc2a938e511cb54, base refs/remotes/origin/main.
Reviewer: real Anthropic CLI claude-sonnet-5-5, effort medium. Single family and
single seat, so this is not an independent cross-family review. Limits: I read
close-and-clean.sh, the SKILL.md/rules/git.md diff and the test tail (all PASS in
the shown tail; I did not read the whole test file). Reproductions ran in a
throwaway fixture under /tmp. Anchor helper was run before and after, source untouched.

Scope contract honoured: targets are explicit branch=full-OID pairs, no target means
no deletion, and I did not ask for global locking or arbitrary-hostile-writer guarantees.

## What holds (checked against code)
- Exact refnames and OID equality are checked before and after the ancestry probe.
  Drift, symrefs, ALREADY-ABSENT and unmerged tips are kept.
- A local tip that moved to an unmerged commit is also caught by `branch -d`
  (HEAD containment with upstream disabled), so the non-atomic window fails closed.
- Remote delete is `--force-with-lease=refs/heads/b:oid` with an explicit refspec,
  so a moved remote tip is refused. The ls-remote suffix-match quirk
  (`x/refs/heads/b`) only produces a mismatch, which reads as DRIFT (safe).
- `b=oid` split on a branch name containing `=` fails validation (safe).
- Removed delete-and-restore, tag-shadowing and parser mechanisms are gone.
- Fetch uses --no-prune --no-prune-tags. A narrow fetch refspec
  (`+refs/heads/main:refs/remotes/origin/main`) with a locally present OID still deletes
  correctly (repro A: local and remote deleted, rc 0). A missing OID makes
  merge-base fail with 128, which the script reports as COULD-NOT-LOOK (safe).

## Findings

### 1. [MEDIUM severity, HIGH confidence] The bare `git fetch origin` runs the user's configured refspecs, and they can rewrite unrelated local branches
skills/roar/close-and-clean.sh:225

Roar's contract is to touch only the completed task's targets. A bare
`git fetch --no-prune --no-prune-tags origin` honours `remote.origin.fetch`. If that
holds a refspec writing into refs/heads/ (mirror-style or `+refs/heads/*:refs/heads/*`),
fetch force-moves foreign local branches. Repro in /tmp/rt1374 with
`remote.origin.fetch=+refs/heads/other:refs/heads/scratch`:
local `scratch` held an unmerged commit 2da8ce6 ("work"); after
`close-and-clean.sh --phase after-exit --local-branch feat=<oid>` (a different branch)
it was 5277f3e (rc 0, "RESULT: clean"). The refs are still in the reflog, but the
tool reported clean while it had moved an unrelated unmerged tip, which is the
behaviour the scope revision forbids.
Fix: fetch only what the check needs, with an explicit refspec that ignores config:
`git fetch --no-prune --no-prune-tags origin "+refs/heads/$DEFAULT:refs/remotes/origin/$DEFAULT"`.
This also removes the dependency on a custom refspec mapping origin/<default> at all.
(`DEFAULT` must be resolved first; the origin/HEAD fallback needs reordering.)
Also: this fetch can still follow tags and run `fetch.recurseSubmodules` / auto-gc,
a lesser side effect.

### 2. [LOW severity, HIGH confidence] Skipped targets are silent
skills/roar/close-and-clean.sh:267-270

A requested target equal to the default branch, current branch, HEAD, or one occupied by
a worktree is dropped with `continue` and no note. The summary line reads
"deleted: none" with RESULT clean (rc 0 if nothing else bumped). The caller
cannot tell "retained because occupied" from "not requested", while SKILL.md says
retained targets are reported. Silence also hides the occupied-branch case the
author asked to preserve.
Fix: emit `SWEEP: RETAINED <ref> (default|current|checked-out)` and `bump 1`.

## Minor
- consider: The remote side leaves the stale `refs/remotes/origin/<b>` tracking ref, and
  SKILL.md says only that absence is checked at the remote ref. Not a safety issue; the next fetch
  without prune keeps it. No action expected.
- nofollow: `branch -d` with upstream disabled keeps targets when HEAD is behind
  integration (documented in SKILL.md; fail-closed).
- nofollow: squash/rebase merges are retained by design (documented).

## Verdict: comment

No reproducible destruction of the targets themselves: unmerged or drifted tips and
occupied branches are preserved. Finding 1 is a reproducible out-of-scope ref rewrite by
the fetch step and should be fixed before merge (one-line change). Finding 2 is a
reporting gap. This is review round 6; it does not approve, reset or waive any gate.
