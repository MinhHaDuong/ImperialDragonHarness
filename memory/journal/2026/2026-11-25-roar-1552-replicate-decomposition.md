# Roar — 1552 /replicate: decomposition, cross-project re-ticketing, padme launch (2026-11-25)

## Context
Ticket 1552 (a /replicate skill for the I4R Replication Games, Toulouse,
2026-12-08) was handed to a background hunt, which stopped at Plan and
proposed a decomposition; the author agreed it was a monster ticket.

## Events
- Split into harness children 1555 (skill), 1556, 1557 (validation runs)
  and 1554 (benchmark), PR #2507. The `replications/` layout was asked of
  the live replicator session by cross-session message instead of a ticket
  written into replicator; it ruled with amendments (replicator 7ad7fe2,
  145d56e: `robustness/` for `probe/`, README, git-ignored `data/`, `out/`
  CSV columns, manifest fields shared with Phase B).
- Author ruling mid-run: a skill does not hardcode its output path; the
  harness defines skills and generic organization, projects implement.
  1555 was amended twice (#2509, #2510) to take the folder from the caller.
- 1555 landed as PR #2511 (gaze REVIEWED, verify-gate APPROVED round 1).
  A resident skill-card budget test (6300 chars, main at 6299) forced the
  hunt to trim four other skill descriptions; total now 6288.
- Author rulings on execution: no commercial software (no Stata), podman
  not docker, no API spending (subscription plans, Pi with local LLM).
  Recorded in 1557 (#2513).
- Replicator-filed 1558 (decision-log skill) was declined: history already
  lives in git log, runtime memory, transcripts and IDH memory; PR #2512
  closed unmerged; replicator removed its `AGENTS.md` pointer (4add205).
- The author asked why harness tickets were worked in another repo: 1554,
  1556, 1557 had only a `design/` summary as harness work. Re-ticketed as
  replicator 0001-0004 (9678126); harness copies closed as moved (#2514).
- Replicator-filed 1559 (ship I4R templates with the skill) accepted, #2515.
  The merge call returned a GitHub 502; the read-back showed MERGED at the
  ruled head.
- Padme: replicator had no remote; pushed to padme over ssh (new `padme`
  remote on doudou), `data/` and the I4R TSV copied, `.env` (API keys) not
  copied. Raid on replicator 0001-0004 launched headless in tmux
  (`claude -p --model opus`, claude.ai auth); first branch observed.
  Hunt 1559 launched the same way on Sonnet.

## Outcome
Skill on main before the 2026-12-05 deadline. Tracker 1552 open; children
1559 (harness) and replicator 0001-0004 in flight on padme.

## References
PRs #2507-#2515; replicator 7ad7fe2, 145d56e, 4add205, 9678126, 217a541.
