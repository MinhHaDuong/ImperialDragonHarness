# Ready-ticket review before a raid: two of five premises had already cleared

2026-10-29. Interactive Imagine review of the five ready tickets (1337-1341),
asked "are they ready to raid?", before raid 6958fe
(2026-10-29-raid-6958fe-resident-budget-composition.md).

- 1337 (after-merge red, pytest-guard): at review time /home was at 12% free
  and `tests/test_shell_init_gh_agent.sh` passed; the red came from
  `scripts/shell-init.sh` printing the disk warning on stdout. The ticket was
  rescoped to the stdout channel (PR 1966) and fixed in PR 1967.
- 1338 (arena skill in contestant pins): `~/.pi/agent/skills/` was already
  empty; the proposed exclusion guard was dropped (PR 1966). Reading
  `harness_pin.py` in the arena repo showed the pin copies
  `~/.pi/agent/skills` and preserves `HOME`; whether a pinned Pi reads the
  live `~/.agents/skills` is untested. Filed as arena ticket 1178, merged on
  arena local main 244f3d2 (no remote). 1338 stays open, not raided.
- 1340 and 1341 (new rule text): the author delegated the decision with
  "Ask Fable for the rest". A Fable advisor (read-only) returned rewrite-then-raid
  for both, moved 1340's denial sentence to `rules/claude-code.md` and placed
  1341 in `rules/workflow.md` § Delegation; its text was applied verbatim in
  PR 1966 and implemented in PRs 1969 and 1970.
- PR 1966 (ticket-only, bookkeeping tier) merged at 21f0f0d3 through
  `raid_land.py` with `attribution: missing`.
