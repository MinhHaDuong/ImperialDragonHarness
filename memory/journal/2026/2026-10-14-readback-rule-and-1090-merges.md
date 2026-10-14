# Read-back rule measured; 1090 merged and closed by hand — 2026-10-14

Project: ImperialDragonHarness. Public audience: repository files, merged
merge requests and counts from session transcripts on padme and doudou.

## Read-back measurement and rule change (#1404)

- Claude Code main threads since 2026-10-01, both hosts: 1,036 forge
  mutations (pushes; merge request create, edit, merge, comment, close).
  231 were read back in the same command, 379 in a separate turn, 391 not
  at all. The 379 separate read-back turns are 2.4% of 15,496 main-thread
  turns.
- 46 mutations were reissued within six calls of a read-back. Of the 26
  printed on padme, none showed a silent failure: the failures among them
  (a rejected force-push, auto-merge disallowed) were visible in the
  mutating command's own output. The 2026-09-04 `gh pr edit` body failure
  that motivated the rule was not re-probed.
- `rules/git.md` now asks for the read-back in the same command. The
  author removed a trailing "not in a turn of its own" clause before merge.
  Merged as #1404 after a rebase and local CI on padme (10 passed); no
  review ran.

## #1403 merge and the 1090 close

- CI's pytest-guard failed on #1403 twice, both from the journal evidence
  folder: ruff on the committed measurement scripts (`.ruff.toml` forbids
  excludes, so the scripts were formatted), and the relocated-clone test,
  which rejects a link to a directory. Another session holding the
  original 1090 work reported both by message and left the branch alone;
  this session fixed and merged it.
- The #1403 body read `**Ticket:** Closes 1090`. `erg-pr-merge` printed
  "No recognised Ticket line … closing nothing" and 1090 stayed open on
  main. It was closed and archived by hand in #1408, merged at once.
- No review ran on #1403, #1404 or #1408, so no attribution records exist
  for them.
