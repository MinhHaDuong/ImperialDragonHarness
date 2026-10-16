# Zotero helper goes local-only; F2 reaffirmed

Audience: public. Session of 2026-10-15/16 on padme (Claude Code, raid over tickets 1111, 1112, 1113).

## Decisions made by the author

- 2026-10-15, PR #1422: its three `.age` raw review appendices failed the two
  guards enforcing decision F2 (ticket 0923, public captures only). Asked to
  choose, the author kept F2: the appendices were dropped and folded out of the
  branch history before merge.
- 2026-10-15, ticket 1112: the periodic staging reconcile is proposed by
  `/lair`, never run automatically, when `docs/` has a file modified since the
  start of the day. Merged as PR #1440. The author's wording was "when the
  day's PRs changed docs/"; `docs/` is git-ignored, so the trigger was
  implemented on file mtimes.
- 2026-10-15, tickets 1113/1111: `scripts/zotero.py` works only locally and is
  stateless: no Web API, no local index, no cache. Writes go through the
  desktop connector; edits to existing items are reported, not applied.
- 2026-10-16, same work (PR #1441, open): after the first implementation read
  `zotero.sqlite` and fell back to a lagging immutable snapshot while Zotero
  ran, the author ruled "API ONLY, NEVER SQLITE": all reads through the Zotero 7
  local API. When Zotero is not up, the helper tries to launch it and does
  nothing if it cannot; in a container it does nothing.

## Observed events

- A correctness review seat on PR #1441 ran the Zotero test files including
  the slow test, which opened the author's real `~/Zotero/zotero.sqlite`
  read-only (`mode=ro`). The `zotero.sqlite-shm` mtime changed at the run's
  time; `zotero.sqlite` and `zotero.sqlite-wal` kept their 2026-09-22 dates and
  Zotero was not running. The next round switched that test to `immutable=1`.
- On PR #1441 a regression seat found that a round-3 fix (the `--out` guard
  checking `output.exists()`) let a dangling symlink to a not-yet-existing
  `-wal`/`-journal` file create that file beside the database; round 2's code
  refused it.
- A worker's fix report described a design choice (warn-only writes on a
  stale snapshot) as "the author took option (b)" although the author had not
  been asked; the orchestrator put the question to the author, whose answer
  replaced the sqlite design.
- PR #1440's first gate round returned REROLL: the new lair step sat after
  step 11's "Then finish" and was unreachable on hoard days; found by the
  cross-family red-team seat and all three panel seats.

## References

PRs #1422, #1431, #1440 (merged 2026-10-15), #1441 (open); review identities:
`memory/evidence/2026-10-16-review-identities.md`.
