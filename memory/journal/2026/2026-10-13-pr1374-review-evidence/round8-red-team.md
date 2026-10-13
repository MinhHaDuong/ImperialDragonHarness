# PR 1374 red-team review, round 8 (author scope revision)

HEAD c3d769ef70a2893063a666d44b2f191186ff5041, base refs/remotes/origin/main.
Round 6 and round 7 reports are archived under .panel/1374/round6 and round7, untouched.
Review round only: no approval, gate reset or merge.

Reviewer: real Anthropic CLI claude-sonnet-5-5, effort medium; one seat. Producer is
OpenAI Sol 6.1, so the producer/reviewer pair is cross-family (as clarified in round 7).
Limits: I read the ddc6210a..c3d769ef diff in full (close-and-clean.sh, SKILL.md, tests,
ticket note). I re-ran only tests/test_roar_close_and_clean.sh at this HEAD: 132 PASS
lines, no other lines (matches the supplied shell 132). I did NOT rerun core-full 1603/4 skip,
preflight 11, fast 960 or lint 185; those figures are the producer's supplied logs and
I make no exact-tip full-run claim. Git 2.53.0 only. Repros ran in /tmp fixtures.

## Round-7 finding (Git 2.53 empty-remote SIGSEGV): verified fixed
skills/roar/close-and-clean.sh:327-343 now uses `branch.$b.remote=idh-roar-head-check-<oid>`
after `git config --get-regexp "^remote\.<alias>\."` (output suppressed). Repros:
- Ordinary merged branch created with `git push -u` (branch.feat.remote/merge set):
  local and remote both deleted, rc 0, no crash.
- Self-tracking branch not merged: UNMERGED, kept, rc 1.
- Late drift (tip moved to an unmerged commit during `branch -d`, upstream also moved):
  "FAILED local seg — Git refused deletion; kept", rc 1, tip preserved, no crash.
- HEAD behind while the tip is in origin/main and its upstream: kept, rc 1 (the documented
  conservative HEAD check; the alias really disables the upstream shortcut).
- Alias collision (only `remote.<alias>.fetch` configured, no URL): RETAINED, rc 1.
- Simulated native SIGSEGV (wrapper killing `branch -d`): "COULD-NOT-LOOK native deletion
  failed for seg (exit 139)", rc 2, branch kept, no preservation claim.
- Occupied and default/current targets still RETAINED (exit 1), re-verified round 7 path
  unchanged by this diff.
- No persistent config written: `git config --get-regexp '^(branch|remote)\.' | grep -c idh-roar`
  gives 0 after runs, and branch.seg.remote/merge unchanged after the drift run.
- The old empty-remote and branch.merge upstream workarounds are not reintroduced.
- A broken ~/.gitconfig-style or .git/config file stops the run earlier with
  COULD-NOT-LOOK (rc 2); I could not make only the alias lookup return >1 in a portable
  fixture, so the `*)` arm at close-and-clean.sh:337 is checked by reading, not by repro.

## Scope
Targets remain explicit branch=full-OID pairs; no target means no deletion; worktree
ownership/exit stays with the caller. No enumeration, locking or generic cleanup added.
The ddc6210a..c3d769ef diff touches only the delete invocation, its SKILL.md paragraph, tests
and a factual ticket note.

## Findings
No blockers. No destruction reproduced.

## Minor
- consider: skills/roar/close-and-clean.sh:322-324 still says "disable its upstream for
  this command"; the code now overrides the remote with an unconfigured alias. Wording only.
- nofollow: the alias name embeds the approved OID, so two runs for one OID share the alias;
  harmless since the lookup requires it unconfigured. No action expected.

## Verdict: approve (this seat's code-review verdict only; not the gate or merge decision)

The round-7 functional gap is fixed with a native-`-d` positive test now passing, protected
and drifting targets still preserved, and no regression found across the round 7 to round 8 patch.
