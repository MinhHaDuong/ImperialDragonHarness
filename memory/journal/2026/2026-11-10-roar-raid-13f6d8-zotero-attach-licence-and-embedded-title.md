# Roar raid 13f6d8: attach licence and embedded-title hint (tickets 1510, 1511; PRs 2408, 2414, 2413)

Date: 2026-11-10. Project: ImperialDragonHarness. No tracker. Follows raid
f7aac3 (tickets 1502, 1503) on the same helper, `scripts/zotero.py`.

## Context

The author launched `raid 1510 1511` from an interface session. Ticket 1510:
`suggest-attachments` compares a file with the parent item before attaching.
Ticket 1511: in `check-staging`, a miss on an embedded PDF title is
`unidentified`, never `absent`. Both edit `scripts/zotero.py` and the same
reference files.

## Events

- Imagine: one reimagine seat on 1510 (claude-opus-5-5), none on 1511, then
  the Blind-Spot seat (claude-fable-5-2) over both. It returned six findings
  the reimagine had not: identifiers used as negative evidence for the first
  time; cwd assumed to be the file's project root; no library lock around a
  check-then-write of about a minute; the sweep left laxer than the hand
  command; restatement sites and pinned tests missing from the list; and, for
  1511, that `audit_one` already retried on the filename, so the red test
  needed a filename of fewer than three words or it was green before the
  change.
- Author rulings during the run, verbatim, logged on the tickets: "Default.
  Multiple DOI and multiple ISBN is the norm." (the sweep keeps its
  behaviour); "Unreliable does not means never use, but use cautiously. LLM
  judgement can be made." (embedded titles; `find-work --metadata` left as
  is); "A good" (1510's refusal on a differing given identifier stands, with
  a way out: record the second identifier on the item and rerun).
- Plans and annotations landed first as ticket-only PR 2408, so both coders
  forked from a main that carried them. Its first `git push` answered
  `! [remote rejected] (failed)`; the same push succeeded on the next call.
  Cause not established.
- The 1511 coder (claude-sonnet-5-5), launched with the one-line hunt brief,
  created no worktree: it committed on the raid's session branch
  `raid-1510-1511-plans` in the raid's session worktree, rebased that branch,
  and returned without verify-adherence, gaze, push or merge request. The
  1510 coder (claude-opus-5-5), launched with the same brief in the same
  message, created `t1510-3878709-30410` and ran hunt to its end. Why the
  first skipped the worktree step was not looked into. The orchestrator
  created branch `t1511-embedded-title-hint` and a locked worktree at the
  coder's commit, moved the session tree to a fresh branch, and ran the
  remaining hunt steps itself.
- A hand run of the live Zotero tests with a display (`DISPLAY=:0`, five
  test files) on the 1511 commit gave 1 failed, 114 passed:
  `test_check_staging_apply_defers_an_orphan_however_complete_its_pdfinfo`
  expected `deferred` for an orphan with complete embedded metadata, which
  the change turns into `unidentified`. `make check` on the same commit gave
  3606 passed, 122 skipped: the live tests skip with "no display" in every
  gate, so no gate showed the failure. The test was updated and the
  `deferred` branch got a live test of its own (a `.bib` entry with a title
  and no author). After the fix: 116 passed.
- The two wave heads conflicted on one line of
  `skills/zotero/references/helper-script.md`. PR 2414 landed first; the 1511
  branch merged main (no rebase, no force-push), the conflict kept both
  sides, and gaze reviewed the merge commit separately. Its differential ran
  `audit_one` from the reviewed head, main and the merged head over 6912
  input combinations: 0 rows differed between reviewed and merged head; 162
  differed against main, all embedded-title misses with no `.bib` title and
  no given key.
- Gaze answered REVIEWED on 2414 (panel, an OpenAI seat) and twice on 2413;
  verify-gate ruled APPROVED at round 1 on both. Both gates ran the touched
  live tests with a display themselves. `raid_land.py` merged 2408, 2414 and
  2413 from the interface session without a permission refusal.

## Outcome

- PR 2414 merged at 7f7e70db3 (ticket 1510 closed); PR 2413 merged at
  3c22a3c3d (ticket 1511 closed); PR 2408 merged at 93c06fdb1.
- Left as decided, named in the requests: the sweep does not refuse on a
  contradicting identifier; with the md5 listing skipped,
  `suggest-attachments --edit` still attaches, says so in the row and exits
  1 (a lead decision, not an author ruling); receipt titles are not treated
  as given; `find-work --metadata` still searches on the embedded title.
- Minor, not fixed: the docstring of `licenses_attach` says
  `suggest-attachments` decides by it, while that command decides by
  `attach_licence`; with the hash index skipped, an embedded-title miss
  reads `unidentified` where it read `unchecked`.
- Defect-fix backfill for 1511 against the records of PRs 2382 and 2399:
  not run. Each record mixes two reviewed heads across its attempts, which
  the sweep runbook counts as unresolved.

## References

Review attribution: `memory/evidence/attribution/2026-11-10-review-attribution-pr2413.md`,
`…-pr2414.md`. Tickets: `tickets/closed/1510-*.erg`, `tickets/closed/1511-*.erg`.
Raid log: `raid=13f6d8` in the repository's raid log.
