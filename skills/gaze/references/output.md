# Gaze — telemetry, force-approve and output shape

Loaded from `skills/gaze/SKILL.md`.

## Telemetry

### Per-phase timing (stderr only)

Each phase emits start/end lines: `[verify] phase=<name> start=<ISO> / end=<ISO> elapsed=<s>s`

### Verdict footer (PR comment)

Appended to the result comment: `telemetry: risk_band=<high|low|normal> wall=<s>s agents=<n> tokens=<in+out> cost~=$<usd>`

Fields: `risk_band`
(path-risk band from the phase-1 `--risk` call — `high|low|normal`), `wall`
(phase 1 to result), `agents` (sub-agent count), `tokens` (sum, use `na` for
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

- Skips review: it spawns no reviewer battery (phases 2–5). Nothing in this run is
  reviewed; the only review the PR has is whatever an earlier round already
  posted, possibly none.
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
risk_band: high|low|normal
circuit_breaker: un-reviewable | waived (<pr_files> content-bearing files / <pr_lines> lines — <reason>) | none
multi_ticket: <distinct close-claim IDs> | none (non-blocking below breaker)
adherence: PASS|FAIL — <n_blocking> blocking | skipped (un-reviewable) | skipped (--force-approve) | skipped (battery NOT-RUN)
review-pr: <n_comments_posted> | skipped (adherence blocking) | skipped (un-reviewable) | skipped (--force-approve) | skipped (battery NOT-RUN)
review-pr scope: one seat | proportional panel | five perspectives | scoped: <objecting perspectives> + regression (omit if review-pr did not run)
panel integrity: COMPLETE|DEGRADED — <PANEL-INTEGRITY: line if degraded>
battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> | skipped (un-reviewable) | skipped (--force-approve)
simplify: <n_fixes_applied> | skipped (adherence blocking) | skipped (prose workpackage) | skipped (un-reviewable) | skipped (--force-approve)

Unresolved review comments: [list or "none"]
Unresolved simplify: [list or "none"]
Adherence: PASS | FAIL (<count>)

next: on REVIEWED, or FINDINGS once fixed, run /verify-gate <pr-number> repo=<caller's checkout>; on ESCALATE, no gate (author decides); gaze is not a gate and does not approve

telemetry: risk_band=<high|low|normal> wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
```

On `--force-approve`, the comment is annotated `FORCE-APPROVED by <reason>`.
