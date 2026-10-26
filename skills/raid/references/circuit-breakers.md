# Raid — circuit breakers

Loaded from `skills/raid/SKILL.md` § Circuit breakers.

All three triggers below require the orchestrator to append a circuit-breaker
note through `erg log <id> "note circuit-breaker — {reason}" <main-repo-tickets-dir>`
to the **main-repo** `tickets/` directory (not the killed agent's worktree copy),
and commit it before relaunching. `erg log` supplies the timestamp and author;
never hand-write the entry. This circuit-breaker placement is separate from
the verdict's `reroll_bump`, which is posed on the PR branch or at merge time.

**Killing a mid-execution agent — salvage WIP first.** Before any
`git worktree remove` on a killed agent's worktree, salvage its work so it
survives the deletion:

```bash
"$IDH_ROOT/scripts/worktree-salvage.sh" <worktree-path>
```

This commits everything on the agent's branch and pushes it. Nothing enforces
the order, so keep it: salvage first, then run `"$IDH_ROOT/scripts/worktree-exit-preflight.sh" --removal --branch <branch> <worktree-path>`. If the guard blocks, retain the tree and surface the reason; otherwise `git worktree unlock` and `git worktree remove` (never
`--force` over uncommitted changes). Relaunch the finisher on the **existing** branch with
`git switch <branch>` (NOT `-c`) — if this follows a killed-agent fork, confirm
the tree with `git rev-parse --show-toplevel` first (rules/git.md § anchor across
a forked-skill boundary); it inspects the salvaged WIP via
`git show --stat HEAD` before continuing rather than starting from scratch.
Salvage is the FIRST step of any restart, not an afterthought.
(memory: feedback_agent_stall_watchdog_recovery)

**Agent timeout**: Record the time of each push and each observed change in
the executor's worktree (compare status snapshots; an already-dirty tree does
not prove recent progress). The ordinary stall window is 10 minutes since
the latest of these. During a declared project gate, check the executor's
worktree with `python3 "$IDH_ROOT/scripts/raid-breaker.py" --worktree <path>
--last-progress-epoch <epoch> --gate-max-seconds <seconds>` before killing it.
A gate run through `raid-gate.py` has a short-lived heartbeat
keyed to this worktree. Hunt's own pre-merge-request run is only the fast
tier, which stays well inside the ordinary window and carries no heartbeat;
a project that declares a longer gate runs it through `raid-gate.py`. Another session's gate cannot excuse this executor,
and a gate in another process namespace is still visible. A heartbeat older
than 30 seconds is stale, not proof of a live gate. `GATE_RUNNING` suspends the ordinary window;
it does not prove a pass. Set the project's maximum above a measured cold gate
run (`gate_max_seconds` in `.idh-checks.json` when present), and record that
budget in the raid log. `GATE_TIMEOUT` means salvage, then kill or escalate;
never grant an unbounded exemption. On gate exit, record the exit time as the
new progress point and resume the ordinary 10-minute window. `STALL` means
salvage the worktree (above), then kill, split or relaunch with narrower scope.
A WIP push after the red test improves salvage but does not exempt the later
gate from this check. Bump reason: `agent timeout` or `gate timeout`.

To be woken instead of polling, run `python3 "$IDH_ROOT/scripts/raid-breaker.py" --wait --deadline <s>
--worktree <path> --gate-max-seconds <s>` as a background command: it exits 1 once on `STALL` or `GATE_TIMEOUT`, never kills
(Claude Code only; decision record in ticket 1214). The window starts at launch.

**Ping-pong detector**: If two agents edit the same file on the
same branch, STOP. Reset to last known-good commit, relaunch ONE agent.
Bump reason: `ping-pong on {file}`.

**Redirect ban**: Do not use SendMessage to redirect a running
agent. Kill and relaunch with corrected instructions.
Bump reason: `redirect ban triggered`.

**Escalation**: If the same fix fails twice, stop and leave a
ticket comment with the two failed approaches.
