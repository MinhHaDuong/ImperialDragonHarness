# Gaze — fork execution contract

Loaded from `skills/gaze/SKILL.md`; applies to every phase that spawns an agent.

## Fork execution contract

`/gaze` runs as a `context: fork` (see frontmatter). A fork's turn ends the
instant it stops calling tools, and **delegated subagents always run in the
background and notify the session, not this fork.** There is no foreground
launch parameter to pass; earlier revisions of this contract named one, and a
lever that does not exist cannot be the thing holding a phase together.

What is true is the first sentence: the fork survives only while it keeps
calling tools. So every agent this skill spawns (the phase 2–5 reviewers and
the review panel's perspective agents) is launched in the background and then
**waited for by polling an artifact it writes**, in one bounded loop. The wait
itself is the tool call that keeps the fork alive.

Each spawned agent is therefore told, in its prompt, to write its result to a
named path under `<worktree>/.panel/<pr-number>/`, writing to `<name>.md.part`
and renaming to `<name>.md`, so a half-written file never carries the final
name. The roster of expected names is written down *before* launching. A
waiter that just gathers whatever files appear cannot tell an agent that
finished silently from one that never started; comparing against a roster
written in advance can.

Without this, the failure is silent and total: the fork ends its turn at the
launch, the completions re-invoke the **MAIN loop**, and the fork's last message
is a fan-out narration ("reviewers are running in parallel…") instead of a
result, with phase 5 never running. This orphaned real runs, each forcing the
caller to relaunch a duplicate reviewer battery.

**Bound every wait, and record what did not arrive.** An agent missing at the
deadline is missing, not clear: name it in the result and treat its phase as
unresolved. Never extend a deadline to avoid recording a gap.

**The contract applies recursively.** Any nested fan-out performed on `/gaze`'s
behalf, such as the review panel's perspective agents, inherits this same rule:
the inner launch must be waited for by polling an artifact too, or the orphan
failure simply moves one layer down. A launch site is bound by the fork contract
whether it is this skill's own or a sub-agent's.

**Caller-side recovery.** If `/gaze <pr>` ever returns a bare fan-out
narration with no `result:` block (REVIEWED/FINDINGS/ESCALATE), treat it as a
non-result: do **not** relaunch the reviewer battery. Wait for the background
reviewer notifications and read the review comment they posted on the merge
request; with that in hand, run `/verify-gate <pr>
worktree=$primary_root/.claude/worktrees/review-<pr-number>`. The gate reads a
waiver only from an already-posted waived `circuit_breaker` header in the PR's
comments, so the recovery needs no extra argument. If none was posted, a waived
15+ file PR is ESCALATE there (fail-safe), as is an un-waived one.

**Fork liveness.** Once the review comment has posted on the PR, the caller must
see the gaze result (returned or posted as a PR comment) within
`fork_liveness_seconds` (`skills/gaze/telemetry.yml`, env override
`GAZE_LIVENESS_WINDOW_S`; default 1200s / ~20 min), same knob pattern as the
wall/token thresholds in § Telemetry. Two independent stalls landed
in exactly this window, both silent: 2026-07-11 (memory
`feedback_agent_stall_watchdog_recovery`) and 2026-07-13 (raid 291-245, PR #551:
the review comment posted, then ~30 min of quiet, no simplify commit, no
result, review worktree mtime frozen).

**On window expiry, do not re-run phases 2–5.** Check three completion markers:
(1) a posted gaze result comment, (2) branch-tip motion on the PR branch, (3) the
review worktree's file mtime. All stale/absent → invoke `/verify-gate` directly,
with the same invocation form as **Caller-side recovery** (one recipe, stated
once). The fallback skips only the redundant phase 2–5 re-execution; verify-gate
runs at full rigor.
