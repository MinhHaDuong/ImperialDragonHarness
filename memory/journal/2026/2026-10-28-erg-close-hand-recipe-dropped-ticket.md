# 2026-10-28 — hand close of ticket 1316 pushed a commit that dropped the ticket

Session: Claude Code, claude-opus-5-5, host padme; raid 76daf8, PR #1924.

Context: before the round-1 verify-gate of PR #1924, the orchestrator closed
ticket 1316 on the branch by hand, following `skills/merge/references/claims.md`
§ Repair: `erg close <ID> <reason>`, then `git add -u tickets/`, then the move
to `tickets/closed/`, then commit.

Events:
- `tickets/erg close 1316 …` inserted the `Closed:` header and moved the file
  into `tickets/closed/` itself (its help text lists the move as step 4). The
  new path was untracked.
- `git add -u tickets/` staged only the deletion of
  `tickets/1316-runtime-py-wake-on-pi-idh-wake-extension.erg`; the guarded
  `git mv` found no file and was skipped.
- The commit `3f7b4118` ("ticket(1316): close and archive — PR #1924") was
  pushed with one change: 26 lines deleted, nothing added under `closed/`. The
  pre-commit `erg check` passed on it.
- `git show --stat HEAD` showed the deletion; the commit was amended to add
  `tickets/closed/1316-…erg` (`34844cdf`, a rename) and force-pushed with lease
  before the gate ran. The gate ruled on `34844cdf`; PR #1924 merged at that head.

Reference: `scripts/raid_land.py` (close step, lines 95-99) runs `erg close`,
`erg archive`, `git add -u tickets/`, then adds `tickets/closed/<id>-*.erg`
explicitly; the scripted merge path stages both sides.

Outcome: no ticket lost on main. The `claims.md` § Repair wording is unchanged
at the time of this entry.
