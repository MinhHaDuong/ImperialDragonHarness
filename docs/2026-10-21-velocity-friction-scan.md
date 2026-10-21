# Velocity friction scan, 2026-10-21

Zero-LLM scan of Claude Code transcripts modified in the last 14 days (2,364
files, main and subagent), prototype not committed (it fails the repo's ruff gate; ticket 1169 writes the real script). Companion to `scripts/trace-stats.py`: that measures
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

## Trend: the 14-day totals overstate the present

Daily Bash calls and guard refusals (tool errors naming the worktree guard),
Bash tool errors only, 2026-10-17 has no transcripts:

| Day | Bash calls | Guard refusals | Write guard | Skill/Grep "no such tool" |
|-----|-----------:|---------------:|------------:|--------------------------:|
| 10-07 | 3762 | 320 (8.5%) | 14 | 7 |
| 10-08 | 2848 | 292 (10.3%) | 14 | 9 |
| 10-09 | 4330 | 431 (10.0%) | 2 | 10 |
| 10-10 | 3045 | 204 (6.7%) | 15 | 9 |
| 10-11 | 718 | 93 (13.0%) | 10 | 1 |
| 10-12 | 611 | 0 | 0 | 0 |
| 10-13 | 6595 | 0 | 0 | 0 |
| 10-14 | 5807 | 206 (3.5%) | 6 | 5 |
| 10-15 | 3023 | 0 | 0 | 8 |
| 10-16 | 2428 | 0 | 0 | 3 |
| 10-18 | 437 | 0 | 0 | 0 |
| 10-19 | 1136 | 0 | 0 | 6 |
| 10-20 | 3939 | 0 | 0 | 26 |
| 10-21 | 2216 | 0 | 0 | 14 |

Reading: every guard refusal and every out-of-tree Write error sits on or before
10-14; none since 10-15. Cause not yet established (a guard change, the
plain-git worktree recipe, or a change of working pattern would each fit); the
guard did not stop refusing because the work stopped, since Bash volume stayed
above 2,000 calls a day. The "no such tool" class is the opposite: it rose to
26 and 14 on the last two days. Ordinary Bash errors run steady at about 3% of
calls. The 14-day totals above are therefore a history, and prices computed on
them (about 1,270 refusals) do not describe the present.
