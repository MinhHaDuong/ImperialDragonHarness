# PR 1374 red-team review, round 7 (author scope revision)

HEAD ddc6210ab38d1b6f2e49f7f4f9c0c92758591ab2, base refs/remotes/origin/main.
Round 6 report (HEAD 3a5fcb31) is archived at .panel/1374/round6/red-team.md and untouched.
This is a review round, not an approval, gate reset or merge.

Reviewer: real Anthropic CLI claude-sonnet-5-5, effort medium.
Metadata correction: the round-6 statement "not cross-family" described this seat alone.
The producer is OpenAI Sol 6.1 and this seat is Anthropic, so the producer/reviewer pair
IS cross-family. I am still one seat with no second reviewer.
Limits: I read the 3a5fcb31..ddc6210a diff in full (close-and-clean.sh, SKILL.md,
tests, ticket) plus close-and-clean.sh from round 6. I ran tests/test_roar_close_and_clean.sh
at this HEAD (117 PASS lines, no FAIL line); I did NOT run the full suite or the
corefullproof / 13 post-doc ratchets, so I claim no exact-tip full run. Reproductions ran in
throwaway /tmp fixtures; the review tree was not written except this file.
Git in this environment is 2.53.0.

## Round-6 findings: verified fixed
1. Configured-fetch overwrite (was close-and-clean.sh:225). Now the fetch is the explicit
   `+refs/heads/$DEFAULT:$base` with `--refmap=` and tags, prune, submodule, auto-gc and
   commit-graph writes off (close-and-clean.sh:254-258). Repro with remote.origin.fetch set to
   `+refs/heads/other:refs/heads/scratch`, `+refs/heads/main:refs/heads/scratch` and
   `+refs/heads/*:refs/heads/*`: foreign unmerged `scratch` stayed at its original tip each time,
   explicit target deleted, rc 0. The symbolic and invalid-default guards are in the added tests.
2. Silent protected targets. Default, current, HEAD and occupied targets are now reported
   as `SWEEP: RETAINED ...` with exit 1 (repro: main on both sides, and an occupied worktree
   branch on both sides, each exit 1, nothing deleted).
3. Regression checks: ordinary local+remote delete (rc 0, both gone), UNMERGED kept (rc 1),
   DRIFT kept (rc 1), ALREADY-ABSENT reported (rc 0). The preflight fail-closed change
   returns 2 on unreadable metadata and is covered by added tests. SKILL.md now uses
   refs/remotes/origin/main consistently and its fetch snippet matches the script.

## Finding

### 1. [MEDIUM severity, HIGH confidence] Local delete never succeeds for a branch with a configured upstream (Git 2.53.0 segfault), so the normal PR-branch cleanup is a no-op
skills/roar/close-and-clean.sh:327

`git -c "branch.$b.remote=" branch -d -- "$b"` crashes with SIGSEGV (rc 139) when `$b` has
an upstream, which is the default state after `git push -u`. Minimal repro without the script:
branch `feat` created with `git push -u origin feat`, merged to main and pushed;
`git -c branch.feat.remote= branch -d -- feat` prints "Segmentation fault", rc 139, branch kept;
plain `git branch -d feat` deletes it. Through the script
(`close-and-clean.sh --phase after-exit --local-branch feat5=<oid>` with feat5 tracking
origin/feat5) the output is "SWEEP: FAILED local feat5 — Git refused deletion; kept", exit 1,
while the remote delete succeeded. Result: the local half of the author's stated purpose
silently degrades to a retained finding for every upstream-tracking PR branch. It fails
closed, so nothing is destroyed, but the message calls a crash a Git refusal.
The tests miss it because the late-drift case (tests/test_roar_close_and_clean.sh:235-252)
expects rc 1 and a surviving branch, which a segfault also produces; no test asserts that
a merged, upstream-tracking branch is deleted. Note this fixture is in the test only
because the SKILL.md rationale reads "disable upstream so HEAD is the check".
Alternatives I tried: clearing `branch.$b.merge` instead does NOT disable the upstream check
(it deleted a branch merged only to its upstream, "not yet merged to HEAD"), so do not switch
to it; clearing both keys also segfaults. Options for the author: (a) add a positive test
for merged+upstream and then pick a form that survives, e.g. check
`git merge-base --is-ancestor "$oid" HEAD` explicitly and run plain `git branch -d`
(the ancestry to origin/main plus OID lease is already verified; plain -d then also accepts
merge to upstream, which only widens the late-drift window to "tip moved to something the
upstream already contains"); or (b) accept the retention and say so in SKILL.md.
I do not claim other Git versions segfault; only 2.53.0 was tested.

## Minor
- consider: SKILL.md says "A checkout behind integration may therefore retain an otherwise
  eligible target"; with finding 1 the behind-HEAD case is not the main retention cause,
  so the wording understates it.
- nofollow: remote-only targets whose objects are not local now return COULD-NOT-LOOK
  (merge-base 128) instead of fetching them, because the fetch is limited to the integration
  ref; this is fail-closed and consistent with the scope contract.

## Verdict: comment

The two round-6 findings are fixed and verified, and I found no reproducible destruction.
Finding 1 is a functional gap in the cleanup the PR exists to deliver (fail-closed), plus a
test that cannot detect it. I recommend fixing or documenting it before merge; it does not
reset or waive any gate.
