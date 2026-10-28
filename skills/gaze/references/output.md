# Gaze — telemetry and the result

Loaded from `skills/gaze/SKILL.md`.

## Telemetry

### Per-phase timing (stderr only)

Each phase emits start/end lines: `[verify] phase=<name> start=<ISO> / end=<ISO> elapsed=<s>s`

### Verdict footer

Appended to the result: `telemetry: wall=<s>s agents=<n> tokens=<in+out> cost~=$<usd>`

Fields: `wall` (phase 1 to result, from `step_clock.py end --seconds <token>`, `na` when not measured), `agents` (sub-agent count), `tokens` (sum, use `na` for
missing), `cost~=` (best-effort USD, `na` if incomplete).

### Duration clock

`gaze_setup.py` starts the clock and prints it as `clock=`; keep the token literally
(shell variables do not persist between Bash calls).
`gaze_close.py --token <clock>` ends it and substitutes the line for `{{duration}}`
in the result file (by hand: `python3 "$IDH_ROOT/scripts/step_clock.py" end <token>`;
add `--seconds` in a second call for `wall=`). Its single line (`duration: 4m12s`, or `duration: not measured`
when no clock could be read) goes into the result block as printed. Never type a duration
from memory or estimate: the line comes from the script or says `not measured`.
This is the one statement of the rule; verify-gate, merge and raid point here.
The plan items' own wall times are the `ran:` line (`seat_clock.py roster`).

### Thresholds

Read from `skills/gaze/telemetry.yml`; env vars override. Defaults: wall
deadline 15 min; tokens warn=500k escalate=1M.

**The deadline is hard.** It runs from the duration clock's start. At the
deadline gaze stops waiting, stops what it can, and goes to verify and output
with what it has: every item not finished is a `not finished at the deadline`
deviation. On tokens warn, add `token-heavy run` to the telemetry line and
continue; on tokens escalate, stop and return ESCALATE with the measured
value.

## Output shape

One result at the end of the run: `gaze_close.py --comment-file` records it as
the review's `answer` entry on notes, the one evidence place (ticket 1301), and
the same text is returned to the caller. On a PR the script posts only a
one-line pointer comment, `/gaze review on notes: <review_id>, verdict <V>`;
a failed post changes nothing. No interim "started"/"finished" chatter.

```
## /gaze result

result: REVIEWED|FINDINGS|ESCALATE
seats: panel|self-only
reviewed_head_sha: <full SHA read from the review tree after the pass>
intent: <the caller's text verbatim | default: the whole merge request against its ticket's exit criteria>
review plan: <method; items as name (model, family); budget> — <why this plan settles the what>
ran: <`seat_clock.py roster` lines, `; `-joined: each item's wall time or `no report (...)`>
{{plan_check}} — <each deviation's reason, and whether the what is still settled>

Findings: [each with its item, severity or tag, location and evidence; or "none"]
Unresolved simplify: [must-fix and consider findings of a simplify item; or "none" | "not planned"]

duration: <the `step_clock.py end` line as printed, e.g. duration: 4m12s>
telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
{{seats}}
```

`{{seats}}` is replaced by `gaze_close.py` with one `seat:` line per plan item that is
a worker, built from the plan's item names and the launcher-set `worker:` headers
(`seat_clock.py identities`, ticket 1303): you type no `seat:` line and no
`reviewer:` line, and a comment with a typed `seat:` line, or without the
placeholder, is refused. The name is the plan item's, the one name used in the
plan, the roster, the `seat:` line and the attribution `seat=` field. The script
also writes the answer's `reviewer:` lines from them, on notes (tickets 1155, 1301, 1307). A `self` item takes the identity given by
`--session-runtime` and `--session-model` of the closing call. A result with no
`seat:` line is a capture failure.
A requested model name is not an observed id.

`seats:` is defined once, in SKILL.md § 4.

`{{plan_check}}` is replaced by `gaze_close.py` with the first line of
`seat_clock.py plan-check`, verbatim; the model writes only the reason after
it (SKILL.md § 5).

`plan check: FAIL` never goes with REVIEWED: a planned item without a report
is an unresolved pass (SKILL.md § 4).
