# Long-run wait language in the harness: audit and alignment

Status: findings and proposed edits, 2026-10-21. No rule or skill was edited;
another session revises the instructions. Companion to
`2026-10-21-await-external-design.md` (the parked waiter design).

Method: an Opus read of rules/, skills/ (SKILL.md and references), AGENTS.md,
profiles/, agents/, adapters docs, and script headers. It read a checkout at
`0bb38be4`, 48 commits behind `origin/main` at the time. For files that moved
(rules/git.md, gaze now split into a core plus references/, merge, raid, hunt,
verify-gate) it re-read `origin/main`. Line numbers marked *main:* are from
main; the rest are from the older tree. Rebase before editing.

## Principle to align on

1. Never block a turn on a foreground sleep, watch or poll loop.
2. Launch long or external work with the runtime's background facility and a
   deadline, so nothing runs forever.
3. Then do in-scope steps or end the turn, and act when the command exits.
4. Read forge state once per step. A bounded loop is allowed only inside the
   background command, or in a context the runtime never wakes (a fork).

What the probes (2026-10-21) say about step 3: only Claude Code re-invokes the
session when the background command exits. Codex background terminals run but
do not wake the model. Pi has no native facility. See the hints list below and
the "Native background, probed" section of the design draft. The principle
therefore has a fallback clause: where the runtime cannot wake the session, the
next step reads the result once.

## Findings

Contradictions (two quoted lines each, in the audit transcript):

| ID | Location | Conflict |
|---|---|---|
| C1 | rules/git.md:24 vs skills/merge/SKILL.md:90, skills/roar/SKILL.md:114 | git.md says "wait for CI" with no mechanism; merge and roar say do not wait on checks. The only resident wait line invites `gh pr checks --watch`. |
| C2 | skills/roar/SKILL.md:43 vs rules/workflow.md:156-158 | Roar on a pending merge says stop and have the user or a later step re-run; workflow says run to the end. Roar makes the author the waiter. |
| C3 | merge/SKILL.md:96-100, erg-pr-status:13, raid/SKILL.md:379 vs memory note no_blocking_waits | Skills: the status command "never loops"; a runtime "may" wrap it in a wake-up. The note: one background command with a hard timeout that exits when the condition is met. The ban must apply to the turn, not to a bounded background waiter. |
| C4 | raid/SKILL.md:307-310 vs 379-380 | Phase 6 polls the verdict artifact in the orchestrator's turn; phase 7 bans any loop or foreground wait. |
| C5 | gaze (main: references/fork-contract.md:9-35), review-pr:41-67, review-pr-prose:39-61 | A fork polls its artifact in one bounded loop. Correct, because background completions wake the main loop, not the fork. It must be a named exception, with a poll cadence (none is given). |
| C6 | rules/authoring-skills.md:38 | "sequential-blocking" reads as permission to block the turn. |
| C7 | hunt/SKILL.md:71-74 | Allows a foreground block in `agent.wait` slices, and "a prompt retrieves the result" makes the author the waiter where the runtime would wake the session. Right as a fallback, wrong as the default. |

Gaps (long task, no deadline or no stated method):

| ID | Location | Gap |
|---|---|---|
| G1 | hunt step 10, scripts/raid-gate.py | The pre-PR gate has no deadline outside a raid (`gate_max_seconds` exists only there). |
| G2 | lair/SKILL.md:58 | `make check` on main: no background, no deadline. |
| G3 | merge/SKILL.md:121-126 (main: 148-153) | Local CI on padme over ssh: no background, no outer deadline. `local-ci.sh:151` caps each job at 1800 s only. |
| G4 | route/references/decorrelation.md:32, routes.json headless templates | Headless seat launches carry no timeout and no background instruction. A detached `nohup` seat sends no notification. |
| G5 | review-pr:155-185, raid:302 | Detached seats have a collection deadline, but the processes do not. |
| G6 | release/SKILL.md:55 | "Wait for all to return": no deadline. |
| G7 | raid:109, 173, 278 | "Wait for all": bounded only indirectly by the stall window. |
| G8 | trace-doctor:44-48 | Shell `&` plus `wait` in one foreground call, unbounded. |
| G9 | external-peer-review/references/openrouter.md:57 | "Run the rest in the background", no deadline. |
| G10 | agents/team-lead.md:16-33 | Spawns executors; no waiting method or deadline. |
| G12 | gaze battery (main: references/battery.md:248-250) | Forge reviewer: "bounded wait of a few minutes", no mechanism. |

G11 (a stale reference to a 30-second polling rule in gaze) is already fixed on
main.

Runtime leaks (a Claude-only or Codex-only name in a portable file):

| ID | Location | Leak |
|---|---|---|
| A1 | hunt:71 | `agent.wait` (Codex tool name). |
| A2 | hunt:104 | `claude -p "/hunt <id>"`. |
| A3 | review-pr:118-124 | `Agent`, `agent.spawn`, `agent.list`. |
| A4 | review-pr:157-160 | `vibe -p`, `claude -p` inline. |
| A5 | route/references/decorrelation.md:32 | "from Claude Code, whose `Agent` children..." |
| A6 | gaze, review-pr, review-pr-prose, verify-adherence, verify-gate frontmatter | `background:` key. Harmless if other runtimes ignore unknown keys (unverified). |
| A7, A8 | raid:291, agents/team-lead.md:19 | Portable files point to `rules/claude-code.md`, which Codex and Pi skip. |
| A9 | scripts/check-agnostic.sh:29-31 | Only `CLAUDE_CODE_*` is caught. `run_in_background`, `Monitor`, `ScheduleWakeup`, `agent.wait` slip through, against rules/authoring-skills.md:16-18. |

Already aligned, keep as is: `erg-pr-status` and the merge, raid and roar
one-shot status reads (pending is a normal answer); the stated seat deadlines in
review-pr, review-pr-prose and the reviewer profiles; raid's stall window and
`GATE_TIMEOUT`; the internal waits in local-ci.sh (1800 s), seat-runner.sh
(600 s), on-start-sync.sh (60 s), the Pi idh-guard, and ci-local. Waits on the
author (perch, aap-annonce, lair, hoard) are out of scope. There is no TUI or
tmux seat-launch instruction anywhere in the harness.

## Proposed edits

`[H]` stands for the pointer `Hints: adapters/runtime-hints.md § Waiting`.
Per-runtime tool names live only in that list.

1. **rules/workflow.md**, new section after "Micro-turn discipline" (about 390
   characters, resident):

   ```text
   # Waiting
   Never block a turn on a foreground sleep, watch or poll loop. Launch long or
   external work (gates, CI, merges, seats) with the runtime's background
   facility and a deadline; then do in-scope steps or end the turn, and act when
   it exits. Where the runtime cannot wake the session, read the result once at
   the next step. A fork polls its artifacts in one bounded loop. [H]
   ```

   Covers C1, C3, C5, C6 and G1 to G10. The audit's draft lacked the fallback
   sentence; the probes make it necessary.
2. **rules/git.md:24** (main): replace "wait for CI" with "CI green (workflow
   § Waiting)". (C1)
3. **merge/SKILL.md:96-100**: "never loops in its turn. To be woken instead,
   run one background waiter with a deadline that re-asks `erg-pr-status` with
   backoff and exits on any answer other than 2. The loop lives inside that
   command, never in the turn. Correctness never depends on the wake-up. [H]"
   (C3)
4. **merge/SKILL.md:121-126**: append "Run it in the background with a deadline
   above its per-job cap times the job waves, ssh included. [H]" (G3)
5. **roar/SKILL.md:43**: on a pending merge, arm the background waiter, end the
   turn, resume from this pre-check when it exits; on timeout report the PR as
   queued. Never hand the re-run to the author. (C2)
6. **raid/SKILL.md:307-310**: seats run in the background with a deadline; the
   orchestrator is woken and then reads the verdict artifact once. Forks poll
   (workflow § Waiting). (C4)
7. **raid/SKILL.md:109, 173, 278**: "Wait for all" becomes "collect on the
   background completions under § Agent timeout; a worker still running at its
   window is salvaged, not awaited." (G7)
8. **hunt/SKILL.md:71-74**: if the runtime wakes the session when the runner
   exits, end the turn and resume then; otherwise wait in bounded slices with
   the runtime's agent-wait facility. [H] (A1, C7)
9. **hunt/SKILL.md:104**: replace the `claude -p` example with "the runtime's
   headless door from `routes.json` `launch_doors`". (A2)
10. **hunt/SKILL.md:140**: run `raid-gate.py` in the background with a deadline
    (`gate_max_seconds` from `.idh-checks.json`, else a measured cold run plus
    margin). Optional: a `--deadline` flag on `raid-gate.py`. [H] (G1)
11. **lair/SKILL.md:58**: `make check` on main in the background with a
    deadline; continue, read the result before the summary. [H] (G2)
12. **route/references/decorrelation.md:32** and **routes.json**: headless
    other-family seats launch in the background with a deadline and an output
    file; a detached process sends no wake-up. Add a timeout note per headless
    door. (A5, G4)
13. **review-pr:118-124, 157-160, 177-183**: replace `Agent`, `agent.spawn`,
    `agent.list` with "the runtime's subagent spawn and list facility"; give
    each seat process a deadline at or just above the collection deadline.
    (A3, A4, G5)
14. **review-pr:66, review-pr-prose:52, gaze fork-contract:16**: the fork poll
    is one tool call that re-checks the manifest every few seconds until
    complete or the deadline, never one call per check. [H] (C5)
15. **release/SKILL.md:55**: collect the three audits under a deadline (about
    15 min); a missing audit is reported missing, never as clear. (G6)
16. **rules/authoring-skills.md:38-40**: "parallel-background or sequential
    (each awaited before the next, per workflow § Waiting)". (C6)
17. **agents/team-lead.md:16-21** and **raid:291**: executors run in the
    background with a deadline; replace the `rules/claude-code.md` pointers
    with "the runtime's concurrency cap [H]". (G10, A7, A8)
18. Optional: wrap trace-doctor's `&` jobs in `timeout` (G8); extend
    `PROSE_PATTERNS` in check-agnostic.sh with `run_in_background`,
    `ScheduleWakeup`, `Monitor`, `agent.(wait|spawn|list)` (A9). The second
    grows a guard, against the severity floor; list only.

Coordination: the Stopguard design plans a `rules/workflow.md` marker line for
its rule 2 (pending wait). Edit 1 should be the anchor that rule cites, so the
two do not land as competing lines.

## Where the hints list lives

The four resident rule files total 17 789 characters against a cap of 17 800
(`tests/test_rules_resident_budget.py:56`), so 11 characters remain, and
raising the cap is a ticket. A new unconditional rules file would be resident
too. Recommendation: `adapters/runtime-hints.md`, loaded on demand and not
scanned by the agnostic checker. Resident cost: the § Waiting paragraph (about
390 characters) plus the git.md change, which needs either a trim in
workflow.md or a small budget-raise ticket (+400).

## Hints list (RUNTIME: FUNCTIONNAME)

Proposed content of `adapters/runtime-hints.md § Waiting`, filled from the
2026-10-21 probes. Cells marked (unaudited) or (unproven) are not verified.

```text
Background command, wakes the session on exit
  Claude Code: Bash run_in_background
  Codex: exec_command + write_stdin (session id; pull within the turn). Probed: a background terminal runs but does not wake the model on exit
  Pi: none native; pi-longrun bg_start + bg_wait (unaudited, 3rd party) or pi-patty-bg-tasks run_in_background (unaudited)

Deadline on the command itself (all runtimes)
  Claude Code: timeout <s> <command>
  Codex: timeout <s> <command>   (yield_time_ms only sets when control returns; it does not stop the process)
  Pi: timeout <s> <command>   (bash tool has no default timeout)

Wake the session from outside (the waiter design, parked)
  Claude Code: background blocker that waits on outcome.json
  Codex: codex queue --thread $CODEX_THREAD_ID --message <text>   (probed; needs the app-server daemon; from a sandboxed shell needs an execpolicy allow rule)
  Codex: functions.exec cell + notify() + functions.wait   (self-reported, within the turn only, not a durable callback)
  Pi: extension sendMessage({triggerTurn: true}) or deliverAs: "followUp"   (unproven here)

Wait on a background subagent
  Claude Code: the completion notifies the main loop
  Codex: agent.wait in bounded slices; sub-agent completion messages reach the parent (self-reported; needs authorization to delegate; alive turn only)
  Pi: subagent tool (synchronous)

No wake-up available: fallback
  Claude Code: n/a
  Codex: read the result once at the next step (write_stdin on the session id)
  Pi: read the result once at the next step

Fork or child poll (the runtime never wakes it)
  Claude Code: one call: timeout <s> bash -c 'until <check>; do sleep 5; done'   (verify that the foreground-sleep block allows it)
  Codex: same, one tool call
  Pi: same, one tool call

Spawn and list subagents; concurrency cap
  Claude Code: Agent; CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH, CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS
  Codex: agent.spawn / agent.list
  Pi: subagent
```

Codex rows marked self-reported come from the model describing its own tools
(2026-10-21), not from a probe. Its account agrees with the probe on the point
that matters: nothing wakes it after the turn ends. Its pattern for a PR
automerge or an external review: a bounded watcher with a command-level
`timeout`, a final state of MERGED, closed unmerged, or deadline reached (pending),
and a reviewer that writes a temporary file and renames it on completion.

## Not checked

The audit did not read tickets/, memory/ beyond filenames, most of docs/ and
of scripts/ usage text, `peer_review.py`, or the adapters' TypeScript beyond a
grep. Unverified: whether Claude Code's foreground-sleep block also catches a
`sleep` inside `timeout bash -c`; whether a team-lead subagent is woken by its
own background children; whether Codex and Pi ignore the `background:`
frontmatter key; the Codex entries `agent.wait`, `agent.spawn`, `notify()`,
`functions.wait` and sub-agent completion messages come from the skills' text or
from Codex's own description and were not exercised.
