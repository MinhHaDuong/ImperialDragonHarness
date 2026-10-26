# Raid — detached gaze sessions

Loaded from `skills/raid/SKILL.md` § Phase 6.

When the runtime's nesting blocks the inline run — a raid is itself
an agent orchestration, and child sessions do not inherit the agent connector;
detect it by the inline run
reporting `battery: NOT-RUN — cause: no-agent-tool`, `depth`, or `guard`,
or by a known absent agent connector — substitute one detached, headless, non-interactive
CLI session per PR per the detached-seat contract
(`skills/gaze/references/panel.md` § Detached-seat substitution): cwd
pinned to the PR's worktree, prompt embedding `/gaze <pr-number>` plus the
caller prerequisites and the containment rails (no merges, no writes outside
the PR branch); the result is observed by polling the written artifact — the
`## /gaze result` PR comment per the output shape in
`skills/gaze/SKILL.md` § Output shape, accepted only when its `reviewed_head_sha`
is not stale against the branch tip (`skills/raid/SKILL.md` § Phase 6) — under that contract's bounded wait, never a spawn exit status,
and the structured result must return to the orchestrator.
