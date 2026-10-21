# Velocity friction scan, 2026-10-21

Zero-LLM scan of Claude Code transcripts modified in the last 14 days (2,364
files, main and subagent), prototype at `docs/2026-10-21-velocity-friction-scan.py`
(run with `python3 -I`). Companion to `scripts/trace-stats.py`: that measures
cost, this measures friction. Baseline census for the same window: 571
sessions, 48.8k turns, about $4.7k shadow cost.

Method limits: durations are `tool_use` to `tool_result` timestamps, so they
include permission waits and background commands; error messages are grouped by
a rough digit and path normalization; the wait-command regex
(`sleep N`, `--watch`, `gh run watch`, `until `) is broad and over-counts.

| Measure | Value |
|---------|-------|
| Bash calls | 41,574; 3,063 errors (7.4%) |
| Worktree-guard refusals (summed by hand over message variants) | about 1,270, roughly 41% of Bash errors |
| Bash calls over 30 s | 2,979, 172.6 h tool wall-clock (upper bound) |
| Commands matching the wait regex | 2,038 (upper bound); hook-blocked `sleep` forms about 43 |
| Skill errors | 85 of 813 calls; 74 are "No such tool available: Skill" in subagents |
| Grep unavailable errors | 15 |
| Write outside the worktree | 59 |
| ExitWorktree errors | 25 of 101 |

Top refusal forms: `git` in a form too complex to verify (324 + 49), `rtk` with
a git command (166 + 125), too complex to verify (145 + 50), git redirected to
the shared checkout (114), `cd` to the shared checkout (67), `sed`/`rtk`/`python`
with a computed value (53 + 51 + 35 + 17).
