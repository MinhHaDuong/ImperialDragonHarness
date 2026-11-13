# Roar PR 2492: DOIfetch pin moved to v0.4.0, shadow extra dropped

Date: 2026-11-13 · host: padme · drafter anthropic/claude-fable-5-2

## Context

The author asked a harness session to ask the session releasing DOIfetch
0.4.0 to notify it directly when done, with no ticket, and then to simplify
the harness side now that DOIfetch no longer depends on bs4.

## Events

- **Coordination by direct message.** The DOIfetch session answered that the
  author had asked it to file a harness ticket; told of the later "no ticket"
  instruction, it filed none. It sent the tag and resolved commit when
  `v0.4.0` existed (tag object f5bb9b7, commit 8e3cc69); the harness session
  read both back with `git ls-remote` before pinning.
- **The change (PR 2492).** `scripts/doifetch.sh` pins `v0.4.0` and runs the
  open and shadow phases from one plain spec. The `doifetch[shadow]` spec and
  its `import doifetch, bs4` probe were removed; on 0.4.0 that probe fails,
  so the old wrapper would have blocked every shadow fallback. `pyproject.toml`
  and `uv.lock` pin commit 8e3cc69. The refusal of a named
  `--source scihub|libgen` (ticket 1549) was kept for its receipt reason.
- **Gate refusal after a post-review fix.** Gaze answered REVIEWED on
  ac3384e with three `consider` findings. One commit took two of them (a test
  for a failing shadow phase's exit code, a memory line). verify-gate then
  refused without spending a round: the commit added test code no gaze answer
  covered. A second, narrow gaze on 21688f7 answered REVIEWED (it mutated the
  shadow `exec` and saw the new test fail), and the gate approved in round 1.
- **Landing.** The first `raid_land.py` call was refused by the permission
  classifier ("Merge Without Review"), gaze and gate having run in the same
  session as forked skills. It ran unrefused after the author typed
  "land 2492". Main tip 1498321 carries a passing after-merge record.
- **Live check.** A direct `doifetch --source scihub --doi ...` on the plain
  `v0.4.0` spec downloaded a PDF (exit 0). A shadow fallback through the
  wrapper's own cascade on 0.4.0 was not run.
- **v0.4.1 announced.** During the review the DOIfetch session announced a
  `v0.4.1` (batch mode exits 1 on a missing data directory) and asked which
  tag to pin. The harness calls the wrapper only with `--doi`, `--isbn` and
  `--version`; PR 2492 landed on `v0.4.0` and the later bump was left to the
  author.

## Outcome

PR 2492 merged at head 21688f7 on 2026-11-13. No ticket was opened or closed.
