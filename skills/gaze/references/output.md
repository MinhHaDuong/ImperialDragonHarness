# Gaze — telemetry, force-approve and output shape

Loaded from `skills/gaze/SKILL.md`.

## Telemetry

### Per-phase timing (stderr only)

Each phase emits start/end lines: `[verify] phase=<name> start=<ISO> / end=<ISO> elapsed=<s>s`

### Verdict footer (PR comment)

Appended to the result comment: `telemetry: wall=<s>s agents=<n> tokens=<in+out> cost~=$<usd>`

Fields: `wall` (phase 1 to result, from `step_clock.py end --seconds <token>`, `na` when not measured), `agents` (sub-agent count), `tokens` (sum, use `na` for
missing), `cost~=` (best-effort USD, `na` if incomplete).

### Duration clock

First action of phase 1: `python3 "$IDH_ROOT/scripts/step_clock.py" start`; keep the printed
token literally (shell variables do not persist between Bash calls).
Last action before posting: `python3 "$IDH_ROOT/scripts/step_clock.py" end <token>` (add `--seconds` in a
second call for `wall=`). Its single line (`duration: 4m12s`, or `duration: not measured`
when no clock could be read) goes into the result block as printed. Never type a duration
from memory or estimate: the line comes from the script or says `not measured`.
This is the one statement of the rule; /verify-gate, /merge and /raid point here.
The seats' own wall times are the `seat times:` line (`seat_clock.py roster`).

### Thresholds

Read from `skills/gaze/telemetry.yml`; env vars override. Defaults:
wall warn=15min escalate=30min; tokens warn=500k escalate=1M. The file's
`fork_liveness_seconds` is not a gaze threshold: gaze never reads it.

On warn: post `/gaze: slow run` comment, continue. On escalate: stop, post
`/gaze stopped:` with measured value. Escalate > warn. Check at phase boundaries
only.

## `--force-approve`

Explicit human override. Usage: `/gaze <pr-number> --force-approve <reason>`.

- `--force-approve` returns `result: ESCALATE` with `battery: skipped (--force-approve)`;
  nothing is reviewed, so REVIEWED is unavailable. The PR comment carries
  `/gaze: force-approved — reason: <reason>` and `FORCE-APPROVED by <reason>`.
- Posts a loud PR comment: `/gaze: force-approved — reason: <reason>`. It lists
  the outputs of phases 2–5 that exist, so reviewers see what was waived.
- Logs the override in the skill transcript.
- Is an override record, not a verdict and not a gate pass: `/verify-gate`
  still rules, and still does not merge.

## Output shape

Post a single top-level PR comment at end of skill. No interim
"started"/"finished" chatter; the final report is the signal.

```
## /gaze result

result: REVIEWED|FINDINGS|ESCALATE
brief: <the brief as received, `default (...)`, or `refused — <reason>`> → ran: <adherence, then each seat that ran, `, `-joined>
reviewed_head_sha: <full SHA read from the review tree after phase 5>
multi_ticket: <distinct close-claim IDs> | none (non-blocking)
adherence: PASS|FAIL — <n_blocking> blocking | skipped (--force-approve) | skipped (battery NOT-RUN)
panel: <n_comments_posted> | skipped (not in brief) | skipped (adherence blocking) | skipped (--force-approve) | skipped (battery NOT-RUN)
panel seats: <perspective> (<family>): clear|concerns|blocking|no report, ... — <why these> (omit if the panel did not run)
seat times: <`seat_clock.py roster` lines, `; `-joined: each seat's wall time, `no report (timed out after <s>s)`, `no report (failed to start)` or `no report`> (omit if no seat launched)
panel integrity: COMPLETE|DEGRADED — <PANEL-INTEGRITY: line if degraded>
battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> | skipped (--force-approve)
review_groups: <group> ← <seats>, ... | one (whole diff)
simplify: <n_findings> on <reviewed SHA> | skipped (not in brief) | skipped (no material growth) | skipped (adherence blocking) | skipped (prose workpackage) | skipped (--force-approve)

Unresolved review comments: [list or "none"]
Unresolved simplify: [list or "none"]
Adherence: PASS | FAIL (<count>)

duration: <the `step_clock.py end` line as printed, e.g. duration: 4m12s>
telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
seat: <role> · runtime=<id> · family=<family> · route=<token> · model=<id as the launch reported it | not observed> · status: ran|failed|skipped
```

The `brief:` line is the caller's check: the left side is what it asked for
(the `brief:` line `gaze_brief.py resolve` printed), the right side what ran;
a seat on one side and not the other is a gaze defect, not a judgement call.

One `seat:` line per review seat launched or planned, retries included, at
column 0 in exactly this shape (a role may hold spaces, never `·`, `=` or `:`): `/roar` writes the PR body's `reviewer:` lines
from them (`attribution_record.py --seats-pr`, ticket 1155). A result with no
`seat:` line, or a body `reviewer:` seat absent from it, is a capture failure. A requested model name is not an observed id.

On `--force-approve`, the comment is annotated `FORCE-APPROVED by <reason>`.

A `panel integrity: DEGRADED` line goes with `result: ESCALATE` (phase 6), never
with REVIEWED: a perspective without a report is an unresolved phase.
