# Weekly ticket audit and a false after-merge red (tickets 1471, 1498, 1500)

Date: 2026-11-09 night, host padme. Interface session on claude-fable-5-2,
at the author's request: review the tickets closed and closing over the last
week for special treatment, friction and complexity.

Scope read: 50 tickets closed between 2026-11-02 and 2026-11-09, the 10 open
ones, and the diff of each landing request.

## What the audit found

- About 40 of the 50 removed or relaxed something or stayed small: the
  cross-PR collision gate retired (1472), 30,546 lines of published
  per-project memory removed (1480), a rule relaxed to practice (1457), one
  idea withdrawn (1441), one reduced to a memo line (1440).
- The rule "git-ignored files count as residue" (ticket 1212) was patched
  four times in eight days (1406, 1458, 1487, 1495), each time for another
  project's ignored build output, seeded data or environment. Its stated
  reason is that a repository may ignore `*`; the harness is that repository.
- The `.tmp` citation gate held about 9.8 GB in arena over an id type check
  (1470). A search of journal and tickets found no block for a real citation;
  blocks are not logged, so the search is weak evidence.
- Ticket 1456 had put one project's filename suffixes (`GTAP WP54`, `AJAE`…)
  into the shared Zotero helper.
- JETP's request for a red-baseline exemption in verify-gate (1471) was filed
  at 21:41Z on 2026-11-08; JETP closed its own baseline ticket 2098 (its
  PR 267) at 22:04Z.
- The after-merge-red ticket template carried one criterion, a passing
  after-merge record, which no gate can read before the merge: 1468 needed a
  reopen and child 1469; PR 2362 got a round-1 REROLL on the same ground.

## The false red on main

After-merge records on 822b9bf2, f6690e42, 72a21fcc, 604349a5 and 459884bd
are `fail` on a sound main. One `merge-gate.py run-after` process (pid
594908, started 22:05:40Z) inherited `TMPDIR` from a roar agent's worktree
(`…/worktrees/roar-5c2a37-2697143-615/.tmp`) when that agent's landing moved
main. The runner serves each new tip for as long as main keeps moving, so the
environment outlived the session. Signatures: 25 failures in 34 s on the
first tip (the directory was gone, `mktemp` failed), then the same five
"outside a git repository" tests in about 690 s per tip instead of about
36 s. The five tests pass in 0.16 s with the default `TMPDIR`. Evidence:
`.git/idh/after-merge.log` (the `tmp_path` values) and
`/proc/594908/environ`. The session owning that agent confirmed the origin by
message.

## Acts

- PR 2363, merged: ticket 1471 closed as denied, reasoning in its log.
- PR 2369, merged: ticket 1500 filed, retiring the ignored-residue rule and
  the `.tmp` citation gate in one request with two commits. Its branch waits
  for ticket 1496's request, which edits two of the same files (agreed with
  the session holding 1496).
- PR 2362, open: `runner_env()` drops an inherited `TMPDIR`. Gaze REVIEWED
  (panel, one OpenAI seat), verify-gate round 1 REROLL, round 2 APPROVED at
  8035e818 after the body changed from a close claim to `Ticket-ref`.
- PR 2370, open: the 1456 suffix list deleted, the after-merge-red template
  reworded. Gaze REVIEWED, verify-gate APPROVED at 3dadaadb.
- sen-causal-reading PR 172, open: ticket 0114 there, telling the project
  that eleven files will read `unidentified` once 2370 lands.

## Refused by the permission classifier

- A comment on PR 2348 carrying the residue-rule argument. PR 2348 was
  landed by another session about forty minutes later.
- `kill -INT` on the runner's process group.
- `raid_land.py 2362` after the author's "Your recommendations as is", which
  followed a report whose first decision read "Land PR 2362 as is, or…". The
  two bookkeeping landings (2363, 2369) ran unrefused.

## Decisions recorded

- Author, 2026-11-09: "Your recommendations as is", on the audit report's
  table and three decisions; then "When done, roar".
- The author's approval covered opening the requests for the suffix list and
  the citation gate; PR 2370 and the 1500 work were not landed on it.
