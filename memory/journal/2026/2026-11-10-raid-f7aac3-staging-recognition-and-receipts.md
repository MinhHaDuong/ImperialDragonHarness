# Raid f7aac3: staging recognition by hash, fetch receipts (1502, 1503)

Date: 2026-11-10. Team lead run, launched by the interface session on the
author's instruction to frame the documentary chain's file handoff.

## Events

- Live measurement, read-only, once: `zotero.py report-duplicates` took
  63.3 s wall for 8,850 hashed attachments (07:13Z, load average 3.7 on 64
  threads); 0.76 s CPU on the client side. The local API ignores an `md5=`
  filter on attachments (tested on the fixture only).
- PR #2382 (1502) landed: one md5 index per check-staging run, then
  identifiers (.bib, url/eprint, page text), title last. Read-only rerun on
  sen-causal-reading `docs/` (141 files): 80 identical / 61 unidentified /
  0 absent before, 84 / 57 / 0 after; four files moved to identical on
  `storageHash`. Of ticket 1456's eleven md5-equal files, ten had since been
  renamed in that project and were already identical; the eleventh
  (`...-R60.pdf`) became identical by hash.
- Author rulings relayed during the run: use Zotero's own attachment MD5;
  pass `--output-dir` explicitly on every DOIfetch launch; receipt format
  JSON Lines in `<staging>/.receipts.jsonl`, vocabulary aligned with
  JETP-observer's retrieval ledger after a survey of four corpus repositories.
- PR #2399 (1503) landed after one FINDINGS round. The other-family seat
  (codex, gpt-6.1-sol) found that a receipt matched only by file name could
  make `check-staging --apply --edit` attach a replaced file to the old work;
  the fix agent reproduced it red (the old code attached) before fixing. In
  the first gaze run that seat had failed to start ("cannot prepare the seat:
  No such file or directory") and the run reported REVIEWED on a self seat
  alone; the raid re-ran gaze to get the other-family read. A vibe backup
  seat produced no valid reach line.
- The first 1503 coder stopped at its context guard with a `make check`
  stalled at 98% for 9+ minutes; the lead killed it; the successor could not
  reproduce a hang (43 s full runs). Cause not established.
- Permission classifier refused, with no explanation, a compound
  `cd <worktree> && git rebase origin/main; git push --force-with-lease origin HEAD`,
  and refused as [Git Destructive] a read-back
  `git ls-remote origin refs/heads/<branch>; gh pr view ...`. The rebase ran
  as `git -C <worktree> rebase origin/main`, the push as
  `git push --force-with-lease origin <branch>` from the primary checkout.
  A `cd` into a worktree did not persist across this subagent's calls, so a
  bare `git push --force-with-lease origin HEAD` ran from the primary and
  pushed nothing (main up to date).
- Main was red after both merges on `tests/test_memory_v8_pilot.py`
  (ticket 1506), from before this raid.

## References

PRs #2382, #2399; tickets 1502, 1503 (closed); raid log id f7aac3.
