# Gaze — telemetry and the result comment

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
The plan items' own wall times are the `ran:` line (`seat_clock.py roster`).

### Thresholds

Read from `skills/gaze/telemetry.yml`; env vars override. Defaults:
wall warn=15min escalate=30min; tokens warn=500k escalate=1M. The file's
`fork_liveness_seconds` is not a gaze threshold: gaze never reads it.

On warn: add `slow run` to the telemetry line and continue. On escalate:
stop and return ESCALATE, the measured value in the result comment. Escalate >
warn. Check at phase boundaries only.

## Output shape

One top-level PR comment at the end of the run, the same text returned to the
caller: the one delivery place. No interim "started"/"finished" chatter.

```
## /gaze result

result: REVIEWED|FINDINGS|ESCALATE
reviewed_head_sha: <full SHA read from the review tree after the pass>
intent: <the caller's text verbatim | default: the whole merge request against its ticket's exit criteria>
plan: <method; items as name (model, family); budget> — <why this plan settles the what>
ran: <`seat_clock.py roster` lines, `; `-joined: each item's wall time or `no report (...)`>
plan check: <the first line of `seat_clock.py plan-check`> — <each deviation's reason, and whether the what is still settled>

Findings: [each with its item, severity or tag, location and evidence; or "none"]
Unresolved simplify: [must-fix and consider findings of a simplify item; or "none" | "not planned"]

duration: <the `step_clock.py end` line as printed, e.g. duration: 4m12s>
telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
seat: <role> · runtime=<id> · family=<family> · route=<token> · model=<id as the worker reported it | not observed> · status: ran|failed|skipped
```

One `seat:` line per plan item that is a worker, at column 0 in exactly this
shape (a role may hold spaces, never `·`, `=` or `:`): `/roar` writes the PR
body's `reviewer:` lines from them (`attribution_record.py --seats-pr`, ticket
1155). A result with no `seat:` line, or a body `reviewer:` seat absent from
it, is a capture failure. A requested model name is not an observed id.

`plan check: FAIL` never goes with REVIEWED: a planned item without a report
is an unresolved pass (SKILL.md § 4).
