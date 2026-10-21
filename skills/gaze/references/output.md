# Gaze — telemetry, force-approve and output shape

Loaded from `skills/gaze/SKILL.md`.

## Telemetry

### Per-phase timing (stderr only)

Each phase emits start/end lines: `[verify] phase=<name> start=<ISO> / end=<ISO> elapsed=<s>s`

### Verdict footer (PR comment)

Appended to the result comment: `telemetry: wall=<s>s agents=<n> tokens=<in+out> cost~=$<usd>`

Fields: `wall` (phase 1 to result), `agents` (sub-agent count), `tokens` (sum, use `na` for
missing), `cost~=` (best-effort USD, `na` if incomplete).

### Thresholds

Read from `skills/gaze/telemetry.yml`; env vars override. Defaults:
wall warn=15min escalate=30min; tokens warn=500k escalate=1M; fork liveness
window=20min (monitored by the caller, not checked at internal phase
boundaries).

On warn: post `/gaze: slow run` comment, continue. On escalate: stop, post
`/gaze stopped:` with measured value. Escalate > warn. Check at phase boundaries
only — except fork liveness, which a silent fork cannot self-check, so the
caller monitors it (§ Fork execution contract).

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
reviewed_head_sha: <full SHA read from the review tree after phase 5>
multi_ticket: <distinct close-claim IDs> | none (non-blocking)
adherence: PASS|FAIL — <n_blocking> blocking | skipped (--force-approve) | skipped (battery NOT-RUN)
panel: <n_comments_posted> | skipped (adherence blocking) | skipped (--force-approve) | skipped (battery NOT-RUN)
panel seats: <perspective> (<family>): clear|concerns|blocking|no report, ... — <why these> (omit if the panel did not run)
panel integrity: COMPLETE|DEGRADED — <PANEL-INTEGRITY: line if degraded>
battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> | skipped (--force-approve)
review_groups: <group> ← <seats>, ... | one (whole diff)
simplify: <n_fixes_applied> | skipped (adherence blocking) | skipped (prose workpackage) | skipped (--force-approve)

Unresolved review comments: [list or "none"]
Unresolved simplify: [list or "none"]
Adherence: PASS | FAIL (<count>)

next: REVIEWED → the caller closes the ticket on the branch, then runs /verify-gate <pr-number> repo=<caller's checkout> session=<uuid> on the current branch head, which is reviewed_head_sha plus at most that ticket-close commit (one re-gate at most, /verify-gate § Gate sessions: a fix asked by the round-1 gate is re-gated once on the new head with the same session=, without a new gaze run); FINDINGS → the caller fixes them and re-runs /gaze on the new head: a head gaze did not review is never gated; ESCALATE (including battery: NOT-RUN or skipped (--force-approve), or a DEGRADED panel) → no gate and no merge: the review never completed, and the PR goes to the author, who decides

telemetry: wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
seat: <role> · runtime=<id> · family=<family> · route=<token> · model=<id as the launch reported it | not observed> · status: ran|failed|skipped
```

One `seat:` line per review seat launched or planned, retries included, at
column 0 in exactly this shape (a role may hold spaces, never `·`, `=` or `:`): `/roar` writes the PR body's `reviewer:` lines
from them (`attribution_record.py --seats-pr`, ticket 1155), and a seat missing
here is a capture failure. A requested model name is not an observed id.

On `--force-approve`, the comment is annotated `FORCE-APPROVED by <reason>`.

A `panel integrity: DEGRADED` line goes with `result: ESCALATE` (phase 6), never
with REVIEWED: a perspective without a report is an unresolved phase.
