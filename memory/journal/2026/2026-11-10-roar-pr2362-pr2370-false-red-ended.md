# Roar: PRs 2362, 2372 and 2370, the false after-merge red ended

Date: 2026-11-10 morning, host padme. Follow-up to
`2026-11-09-weekly-ticket-audit-and-false-red.md`; same interface session,
claude-fable-5-2.

- The stale after-merge runner (pid 594908) had exited by 06:50Z. It left
  `fail` records on 51490c1d, e11ba9a4 and 0de81b3a as well as the five tips
  already listed.
- The author said "merge 2362". `raid_land.py 2362` ran unrefused this time
  and read back MERGED at 8035e818 (main 4e300663). The same command had
  been refused by the permission classifier the evening before, after the
  author's "Your recommendations as is".
- The runner started by that landing had `TMPDIR=/scratch/tmp` and recorded
  `pass` on 4e300663 at 06:54Z, pytest-guard in 29.9 s.
- PR 2372 (ticket-only) closed ticket 1498 on that record.
- The author said "merge 2370"; it read back MERGED at 3dadaadb (main
  2031b778), after-merge record `pass`, pytest-guard in 30.1 s. New
  after-merge-red tickets carry the reworded criterion from this tip on.
- The author then asked why the staging check does not read the first page.
  Reading `scripts/zotero.py`: `audit_one` uses the `.bib` entry, the
  container Title and the filename; `extract_one` already reads page text for
  identifiers; `find_work` compares the file md5 only with works found by
  another key. The author approved the principle (hash lookup, identifiers
  from page text) and asked for the whole documentary chain to be framed
  before a ticket is filed and raided.
