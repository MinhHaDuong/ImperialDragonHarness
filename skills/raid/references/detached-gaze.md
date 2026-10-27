# Raid — detached gaze sessions

Loaded from `skills/raid/SKILL.md` § Phase 6.

When the runtime's nesting blocks the inline run — a raid is itself
an agent orchestration, and child sessions do not inherit the agent connector;
detect it by the inline run's `plan check: FAIL` naming seats that could not
launch, or by a known absent agent connector — substitute one detached, headless, non-interactive
CLI session per PR per the detached-seat contract
(`skills/gaze/references/panel.md` § Detached-seat substitution): cwd
pinned to the PR's worktree, prompt embedding `/gaze <pr-number> <intent>`, the
intent passed verbatim on every runtime (Claude Code, Codex, Pi), plus the
caller prerequisites and the containment rails (no merges, no writes outside
the PR branch); the result is observed by polling the written artifact — the
`## /gaze result` PR comment per the output shape in
`skills/gaze/SKILL.md` § Output shape, accepted only when its `reviewed_head_sha`
is not stale against the branch tip (`skills/raid/SKILL.md` § Phase 6) — under that contract's bounded wait, never a spawn exit status,
and the structured result must return to the orchestrator.

## No result

No `result:` block is no result. Wait for the background reviewer
notifications and read the review comment they posted on the merge request;
that comment is evidence, not a gaze result, and opens no gate. Run
`/gaze <pr>` once more if the liveness window allows; otherwise park the
merge request and escalate to the author.

**Fork liveness:** once the review comment has posted, the gaze result
(returned, or posted as a PR comment) is due within `fork_liveness_seconds`
(`skills/gaze/telemetry.yml`, env override `GAZE_LIVENESS_WINDOW_S`). On
expiry, do not re-run gaze's pass: check the three completion
markers, a posted gaze result comment, branch-tip motion on the PR branch
and the review worktree's file mtime. All stale or absent: no accepted gaze
result, so no gate; park the merge request and escalate to the author. Never
substitute a direct `/verify-gate` for the missing result.
