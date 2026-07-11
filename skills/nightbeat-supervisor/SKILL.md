---
name: nightbeat-supervisor
description: Supervise an overnight autonomous work run: keep the authorized ticket queue moving, integrate verified work, diagnose and repair failures, and deliver a self-contained morning report. The nightbeat supervisor governs by intent — a goal and three hard invariants bind; every mechanism (frequency, wake-up, delegation, building blocks) is the executor's declared choice.
user-invocable: true
argument-hint: "[--since ISO-TS]"
---

# Nightbeat Supervisor

This skill is an intent-based contract (mission command): the **Goal** and
**Invariants** below bind the run; everything else is the **executor's
latitude**, exercised and declared at run start. The mechanisms named later in
this file are illustrative defaults, not the contract.

## Goal

**Doctrine — autonomous mode trades supervision for time.** The run loses the
human eye but is freed from the interactivity constraint: nobody is waiting on
the next reply. The executor therefore shifts its operational cursor toward
spending that freed time on verification — more independent verification
passes than an interactive session would afford (independent means a different
lens or a different agent, never the producer re-reading itself) — and, when
confidence is low or a judgment call exceeds its depth, escalates, including
consulting a more capable agent for advice, instead of guessing.
Cheap-but-plausible loses to slow-but-verified; the deadline is dawn, not the
next message. The invariants below follow from this premise.

Advance, overnight, the ticket perimeter the author authorized, without
crossing any human-in-the-loop boundary, and deliver a self-contained morning
report.

## Invariants (the only prescriptions)

1. The queue is *live*: a ticket filed during the run enters the perimeter if
   its lineage traces to an authorized parent; tickets labeled needs-human or
   deferred are always excluded.
2. Nothing integrates without verification, and verification depth scales
   with the time available — overnight, that means multiple independent
   passes, not a single self-check; a failure is diagnosed then retried or
   re-ticketed, never swallowed.
3. The bounds set at launch (perimeter, cycle/budget ceiling, prohibitions)
   are hard.

## Executor's latitude

Frequency, wake-up mechanism, work decomposition, delegation, and choice of
building blocks — whatever their current names — are the executor's decisions,
declared at run start. Per the reuse gate in `rules/workflow.md`, that
declaration states which existing skills or runbooks are reused, or why none
fits. Capabilities the executor typically composes: schedule a wake-up, list
ready tickets, delegate work to a subagent, run the verification gate,
integrate a merge request, append to a journal.

---

# Illustrative defaults

Everything below is **one possible organization** — the arrangement proven in
production so far — offered as a starting point under the executor's latitude.
An executor may replace any of it, provided the invariants hold.

**Default cycle shape**: survey → integrate ready work → diagnose and repair →
escalate → journal. The steps run **sequentially within a cycle** — each
consumes the previous step's output. Merge candidates within the integrate
step are also **sequential-blocking** (each integration moves the base the
next one lands on). Independent failure diagnoses may be delegated to
**parallel** subagents, within the concurrency cap in `rules/workflow.md`.

**Default working discipline**:

- Never integrate without an APPROVED verdict from the verification gate
  (this instantiates invariant 2).
- Instantiate invariant 1 by re-listing ready tickets at every wake-up rather
  than fixing an itinerary at launch — a child of an authorized parent filed
  mid-run is in scope on the next cycle.
- Stop the run's scheduler before editing the cycle-runner code, restart it
  after; never edit skill definition files mid-run.
- **Commit tracked writes immediately.** Every write to a tracked file in
  `$HARNESS_DIR` (`settings.json`, `scripts/beat.py`, `tickets/*.erg`) must be <!-- harness-extension-point -->
  followed by `git add <file> && git commit -m 'chore(supervisor): <description>'`
  before proceeding to the next action. Uncommitted tracked files cause the
  next cycle's dirty-tree pre-flight to abort.
- **Commit on a branch, not main.** If `$HARNESS_DIR` is the **primary**
  checkout, its pre-commit hook refuses commits on `main` (everything lands
  via branch + merge request). Before the first supervisor commit in a cycle,
  ensure `git -C $HARNESS_DIR rev-parse --abbrev-ref HEAD` is not `main`; if
  it is, `git -C $HARNESS_DIR switch -c supervisor-$(date +%F)` — and open a
  merge request for the accumulated chore commits rather than pushing to main.
  (Commits made from an isolated worktree are unaffected; the guard only fires
  in the primary checkout.)

## 1. Survey

Pre-flight: probe the primary checkout (ticket 0247). A run that died
mid-flight can strand the harness checkout off main with a dirty tree,
silently blocking the daily-pull schedule and every later cycle's dirty-tree
pre-flight:

```bash
$HARNESS_DIR/scripts/check-primary-checkout.sh "$HARNESS_DIR"
```

Non-zero means stranded (off main, or dirty beyond settings.json). The
consolidation commit is safe on its branch, so `git -C "$HARNESS_DIR" switch
main` restores the position; if the tree is dirty for another reason, diagnose
or escalate rather than proceeding — cycles keep failing until it is clean.

Pre-flight: verify no dual-journal state exists (`canonical` vs `logs/` path).
If both `<project>/nightbeat-supervisor-journal.jsonl` and
`<project>/logs/nightbeat-supervisor-journal.jsonl` exist as independent files
(not a symlink), stop and open a ticket before proceeding. The survey helper
enforces this automatically and exits non-zero if the condition is detected.

```bash
python3 $HARNESS_DIR/scripts/nightbeat-supervisor-survey.py [--since ISO-TS]
```

If `--since` is absent from `$ARGUMENTS`, the helper derives the watermark
from the latest `ts` in `$HARNESS_DIR/nightbeat-supervisor-journal.jsonl`
(defaults to 24h ago if no journal exists). It reads
`$HARNESS_DIR/logs/beat-outcomes.jsonl` and finds open merge requests for
succeeded tickets via remote branch lookup and the forge API. Outputs
`{prs_to_merge, failures, watermark_ts, journal_context}`.
If both lists are empty, write a journal `action=idle` entry and stop.

## 2. Integrate ready work

For each entry in `prs_to_merge` (which includes the merge-request number,
the forge repo identifier, and `project_path` derived by the survey helper
from the project's git remote), sequentially:

1. `bash $HARNESS_DIR/skills/nightbeat-supervisor/check-pr-diff <pr_number> <github_repo>`
   — non-zero exit is a HOLD; add to failures with the helper's reason.
2. In the target project (`cd <project_path>`), fetch and check out the
   merge-request branch with the forge tooling of the day. <!-- harness-extension-point -->
   Then run the verification gate on the merge request:
   APPROVED → integrate it with the merge capability.
   REROLL → append the failing criteria as a note on the linked ticket
   (create the ticket if none
   is referenced in the merge-request body), then commit the ticket file:
   ```bash
   cd $HARNESS_DIR
   git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): append REROLL note to <ticket>'
   ```
   and move on. ESCALATE → go to step 4.
   After the gate and integration complete, return to `$HARNESS_DIR` for the
   next candidate.

## 3. Diagnose and repair

For each failure, read the cycle log and ask **why** until you reach an
actionable root cause:

> Why did it fail? → Why did that happen? → Why was that condition present?

When you reach a root cause, repair if within authority:

- **Missing permission** → add to the `settings.json` allowlist, then
  `git add settings.json && git commit -m 'chore(supervisor): add <permission> to allowlist'`.
- **Budget too small for the actual scope of work** → before raising, apply
  the convergence guard:
  1. Count `action=repair` journal entries for the same project+phase in the
     last 7 days. If ≥ 3: **do not raise**. Instead, open a ticket:
     "budget not converging for {project} {phase} — {N} raises in 7 days,
     current={current}, started={first}."
     Then `git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): convergence ticket for <project>'`.
  2. If the proposed raise would exceed 1.5× the module-level constant for
     that phase, log a warning and include it in the ticket body (note: the
     hard ceiling remains 2× the module-level constant — the 1.5× threshold
     is a warning only, not a new cap).
  If neither guard triggers: raise the per-project `ProjectConfig` field in
  the cycle-runner (`beat.py`) by 20%, capped at 2× the module-level
  constant; never touch the module-level constant. Then
  `git add scripts/beat.py && git commit -m 'chore(supervisor): raise <field> budget for <project>'`. <!-- harness-extension-point -->
- **Timeout during verify/review** (`outcome=timeout` AND why-chain
  shows verify/review slowness, not implementation slowness) → raise
  `raid_timeout_s` in the per-project config by 20%, capped at
  2× `RAID_TIMEOUT_S` (3600 s). Then
  `git add scripts/beat.py && git commit -m 'chore(supervisor): raise raid_timeout_s for <project>'`. <!-- harness-extension-point -->
  Implementation slowness is a "ticket too
  large" signal — do not raise the timeout for that.
- **Ticket too large to finish in one cycle** → split into one ticket per
  independent unit of work; leave the parent open as an umbrella. Each child
  ticket must carry `Blocked-by: <umbrella-id>` so the ticket picker can
  auto-close the umbrella when all children are done (it uses inverse lookup,
  not a `Blocks:` header — that header is not valid in %erg v1). Commit the
  new ticket files by naming each child (`git add tickets/<child-id>-*.erg`,
  one per child), then
  `git commit -m 'chore(supervisor): split <ticket> into children'`
  — never `git add` over the whole `tickets/` glob, which also sweeps a stray
  `.erg` left by another agent in the shared checkout.
- **Dead wake-up scheduler** → restart it.
- **Dirty working tree** (`outcome=aborted-dirty-tree`) → if the dirty files
  are machine-local state (beat-outcomes.jsonl, STATE.md, build artifacts),
  commit or stash them; otherwise open a ticket naming the dirty files and
  their likely source, and `git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): dirty-tree ticket'`.

If the why-chain bottoms out without reaching anything repairable: escalate
(step 4).

**Anything else**: open a ticket stating the root cause chain; do not
auto-repair. Then `git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): ticket for <root-cause>'`.

## 4. Escalate

Triggers: ESCALATE from the verification gate, why-chain without a repairable
finding, or the same root cause recurring ≥ 3 consecutive runs for a project.

Call an advisor capability if available; otherwise delegate to a
strong-reasoning subagent with the log context. Create a
ticket with the verdict if the fix is outside authority. Commit the ticket:
`git add tickets/<ticket>.erg && git commit -m 'chore(supervisor): escalation ticket for <project>'`.

## 5. Done

Append one journal entry per action taken this cycle to
`$HARNESS_DIR/nightbeat-supervisor-journal.jsonl`. If no actions were taken,
append a single `action=idle` entry — this serves as the watermark so the
next cycle knows where to resume.

**Clean-tree guard.** Before printing the summary, run:
```bash
cd $HARNESS_DIR
dirty=$(git status --porcelain)
if [ -n "$dirty" ]; then
  echo "WARNING: supervisor leaving dirty tree: $dirty"
  git add -u && git commit -m 'chore(supervisor): commit residual tracked writes'
fi
```
This is a safety net — every write should already be committed by the steps
above. If the guard fires, it means a write point was missed; log the warning
so the next morning report flags it for a skill fix.

End with:

```
supervisor: <ts> — merged: N, repaired: N, tickets: N, escalated: N
```
