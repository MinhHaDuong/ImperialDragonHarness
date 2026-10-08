---
name: raid
description: "Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears."
disable-model-invocation: false
user-invocable: true
argument-hint: '[ticket-ids or "all open"]'
---

Orchestration with ordinary judgment; choose workers per the `route` skill (`skills/route/SKILL.md`).

# Raid $ARGUMENTS — Imperial Dragon hunt

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

A raid does not redefine skills. It calls `/hunt`,
`/review-pr`, `/roar`, etc. Its job is sequencing, wave management,
and enforcing invariants.

## Model policy (rightsizing)

Name a role for every launch and choose the worker for it with the `route`
skill (`skills/route/SKILL.md`), which owns the grid, the route cache and the
launch-choice rule. Skill frontmatter does not configure spawned children.
Favor cheap workers for broad fan-out and reserve the strongest advisor for
difficult judgments.

- **Workers and mechanical helpers:** cheap workers; keep mechanical verdicts
  concise.
- **Planning, review, and orchestration:** mid-tier workers; promote difficult
  cross-ticket judgment to a stronger one when needed.
- **Execute:** the coder profile (`agents/coder.md`, pinned `model: strong`) for
  difficult repository mutations; use a cheaper worker for bounded tasks.
- **Advisor:** the strongest available advisor, at standard effort
  (intensive only rarely: it multiplies cost for marginal judgment), as a
  one-shot call with a self-contained brief on a
  deep, well-defined problem: a ticket that can be neither done nor split, a
  review of a scientific argument and its methods, or a design review of a
  critical feature. Never a standing setting of the orchestrator or a fan-out
  member.
- **Per-ticket `/gaze`:** respect that skill's declared reviewer intentions.

Choose the least expensive worker adequate for the responsibility. Model
identities and provider-specific effort controls belong to the `route` skill
and runtime configuration.

## Balance rule

**Deliverable work ≥60%, tooling ≤40%.** If two consecutive tickets were tooling, the next must advance a deliverable. Track in session log.

**Deliverables**: whatever the project's north star names as its product. For a *science* project that's papers, slides, reading notes, figures, responses to reviewers — and tooling (tests, hygiene, refactoring) is the supporting infrastructure the rule throttles. For a *tooling/library* project (e.g. this harness, git-erg) the product **is** the skills, rules, tests, and helpers — that work is the deliverable, not the throttled category, and the ratio does not apply. Read "deliverable" off `STATE.md`'s north star, never off a fixed papers/slides list.

**Escape hatch**: if `make check-fast` fails and blocks all deliverable work, tooling may exceed 40%. Document why.

## Checkpointing

Every phase ends with a git commit. If the session dies, resume by
reading the ticket logs and git history to determine which phase
completed last. The checkpoint is the repo, not session state.

## Phase 1: Select

If $ARGUMENTS is "all open": read open tickets from git-erg `tickets/` or forge.
Otherwise: parse comma-separated ticket IDs.

Prioritize:
1. North-star deliverables first (what the project's product is — manuscripts/figures for a science project, skills/rules/tests for this harness or git-erg; see § Balance rule)
2. Gaps with north star (STATE.md)
3. Ripest open issues
4. Inline markers (FIXME, TODO, HACK)

Read each ticket + STATE.md. Group by milestone. Identify dependency order and wave structure.

**A skip-labelled ticket is never a raid target.** `tickets/.ergrc` lists the
labels that hold a ticket back (`needs-human` and `deferred` at present) and
`erg ready` suppresses every one of them. Phase 1 reads `tickets/` directly and
bypasses that filter, so the exclusion is this skill's own job: a ticket carrying
`Label: needs-human`, or any other header listed in `.ergrc`, is dropped before
wave grouping, with no Imagine agent, no plan, no Phase 5 executor. Read the
label set from `.ergrc` rather than hardcoding it here — and if that file has
no readable `[labels]` section, fall back to the documented defaults
(`needs-human`, `deferred`). An *absent* `.ergrc` already falls back inside
`erg`, but an *empty* `[labels]` section fails open, and a hand-parse that
inherits that asymmetry screens nothing while looking correct.

Such a ticket is not lost. Name it in the wrap-up briefing with the decisions
it is waiting on, and count that as a success outcome — the same standing hunt
step 2b gives a returned batched decision list.

**Carve-out: an explicit `/raid <id>` runs.** The exclusion governs target
*discovery* (the "all open" path), never a ticket named by ID. A named ticket
is a caller's deliberate choice, so it executes; note the override in the
briefing so the choice is visible.

Do not read that carve-out as "explicit means the author asked." The
explicit-ID shape covers an author typing it and a program building it alike,
and this skill cannot tell them apart. The autonomous caller that used to exist
was safe for a reason that lived upstream of here, not in this phase: its
candidates came from `erg ready`, which already applies the skip filter. That
caller was removed with the nightbeat block (ticket 0882), so there is none
today — and any future one that synthesizes IDs some other way needs its own
screen before it reaches this carve-out.

If EVERY discovered ticket is skip-labelled, the run returns those batched
decision lists rather than an empty-run report. One question round the author
can answer in a single pass is the deliverable (decided 2026-07-28, ticket 0390).

Apply the monster-ticket checklist (`rules/workflow.md` § Autonomous action) to each candidate before wave grouping; decompose monsters into tracking + child tickets rather than holding them or fanning them into a colliding wave.

## Phase 2: Imagine (parallel)

For each ticket, launch an agent (background, no isolation needed — read-only;
mid-tier worker per § Model policy):
- Read ticket + STATE.md + surrounding code
- Reimagine: why now, why this scope, what's the simplest path
- **Antipattern scan (scope).** YAGNI (search the package registry —
  don't hand-roll what a library already does), premature abstraction.
  Annotate any hits with the proposed fix.

Wait for all.

### Blind-Spot pass (cross-ticket)

Before committing the reimagined tickets, launch **one** additional read-only
agent (mid-tier worker per § Model policy) over the original tickets **and all
Imagine outputs together**. Its job is not to review implementation quality or
repeat the per-ticket critique. It challenges the *search space the Imagine
team considered*: what important thing did the whole team fail to look for?

Probe explicitly for material omissions in:
- hidden or shared assumptions and alternative framings;
- stakeholders, users, or downstream consumers absent from the discussion;
- evidence, data sources, counterexamples, or regime changes that could reverse
  a recommendation;
- credible alternative approaches or dependencies nobody considered;
- failure modes, boundary cases, and common-mode reasoning shared by several
  Imagine agents.

Report only omissions that could change scope, priority, feasibility, or the
recommended path. For each finding give: **omission → why it matters → smallest
follow-up check/question**. Do not manufacture novelty and do not restate risks
already surfaced by the Imagine agents. If nothing material is missing, return
`BLIND-SPOT: CLEAN`.

Feed each material finding back into the affected ticket's Imagine annotation
before the drift guard below. The Blind-Spot pass has the same intent boundary
as every Imagine agent: it may expose a missing premise or recommend a simpler
implementation path, but it may not invent a new deliverable or substitute the
author's goal. A finding that requires new intent is returned to the author,
not silently written into the ticket.

Commit reimagined tickets. Report scorecard, including the Blind-Spot verdict.

**Drift guard**: For each reimagined ticket, compare against the original:
- Exit criteria dropped or reworded to change intent → ESCALATE.
- New exit criteria added that weren't implied by the original → ESCALATE.
- Scope narrowed to a strict subset of the original → allowed (simplification).
- Implementation approach changed but exit criteria preserved → allowed (that's the point).
- Premise objection (the agent recommends *not executing*, citing the specific
  commit, config, or regime change that voids the ticket's premise) →
  **return to author** with the evidence. A success outcome of this phase,
  not a guard violation.

The what belongs to the author; the how belongs to the agent. An Imagine
agent never edits intent: no new deliverables, no substituted goals. But
delivery presumes the ticket's premises still hold, so check "why now"
against the current tree and regime — what merged, what changed on the
ticket's surfaces since its Created date. A ticket whose premise has expired
is returned to the author with the evidence; that return is the phase doing
its job, not drift. Any ticket that fails the drift guard is pulled from the
raid and left for human review with a comment explaining what the Imagine
agent proposed to change and why.

## Phase 3: Plan (parallel)

For each reimagined ticket, launch an agent (background; mid-tier worker per
§ Model policy):
- Read ticket + actual source code
- Write Actions, first test, dependencies
- **Antipattern scan.** Tautological tests — would this test catch a
  wrong implementation, or only a different one? Annotate any hits
  with the proposed fix.

Wait for all. Commit planned tickets. Report scorecard. Ticket files go on a
branch — stage and commit the `.erg` file immediately after writing it; if
staging fails (gitignore or wrong cwd), embed the ticket content directly in
the execute agent prompt and the agent creates the file as its first step.

## Phase 4: Verify feasibility

Launch agents by cluster to cross-check plans (a cheap worker for the mechanical
existence checks — paths/lines/signatures; a mid-tier worker for the cross-ticket
conflict and cross-cutting-registry scan, which is judgement across N plans, not
lookup — missing it cost a resurrection agent for 3 of 4 merges, see § Phase 5.0
below):
- File paths, line numbers, function signatures
- Data assumptions, API key requirements
- Cross-ticket conflicts
- Cross-cutting registries: a file holding a shared hash-set / dict / dispatch
  table (test allowlist, dispatch keys, config conventions) that 3+ PRs will
  edit. Flag any you find — they trigger the Phase 5.0 coordination PR.
- Planned-PR size: for each plan, count every path its PR diff will touch
  (ticket and test files included — the breaker counts them) and compare with
  the `/gaze` un-reviewable breaker (`skills/gaze/SKILL.md` phase 1 Setup;
  threshold (15+ files) owned by `rules/workflow.md` § Ticket discipline for
  multi-PR work, restated here only so the drift-pin test can catch it). A
  planned PR reaching the breaker gets WARN plus a proposed split into child
  PRs before Phase 5 spawns executors.

Annotate tickets with PASS/WARN/BLOCK. Commit annotations.

After committing the final annotation, run `git pull --rebase origin main`, then
record `WAVE_BASE="$(git rev-parse HEAD)"` in the raid log. Per-phase annotation
commits stay as they are — WAVE_BASE is simply their last commit — so every wave
ticket annotation is an ancestor of it and all wave branches fork from one
shared, mergeable base. Patch-equivalent commits are not merge-equivalent: the
2026-10-02 raid carried the same annotation patch as 26c8ab73 (native) and
635cf70c (cherry-pick), and every pair of wave PRs holding different SHAs of
that one patch collided on the ticket files at merge time.

## Phase 5.0: Land coordination PR (cross-cutting registries)

**When**: 3+ PRs in a wave will edit the same file holding a shared
hash-set / dict / dispatch registry (test allowlists like `VALID_ROUTES`,
dispatch keys, config-file conventions). If ≤2 PRs touch it, skip — a manual
rebase is cheaper than the coordination overhead.

**Why**: when N parallel PRs each append to the same cross-cutting set, the
rebase onto sibling-merged main silently drops each PR's own addition. Wave 2
(SOTA-adapter raid, 2026-05-20) needed a resurrection agent for 3 of 4 merges
because of this.

**How**: before opening any Wave-N PR, open one tiny PR that adds ALL of the
wave's entries to the shared registries at once, and merge it first. Each
Wave-N PR then makes a purely additive change (new file, new entry referencing
a pre-registered key) without mutating the shared set. The coordination PR
itself follows the normal verify/merge gates.

## Phase 5: Execute (waves, worktree-isolated)

Group tickets into waves:
- Wave N: no unmerged dependencies
- Wave N+1: depends on Wave N results

**Wave base**: every wave branch forks from WAVE_BASE exactly — executors
spawn from the main checkout sitting at WAVE_BASE (Phase 4), never from
whatever origin/main has drifted to since.

**When**: origin/main advances mid-wave, after executors have already forked.

**Why**: a branch forked before or after the advance carries a different SHA of
the annotation commits, and patch-equivalent commits are not merge-equivalent —
divergent copies collide on `tickets/` at merge time.

**How**: the orchestrator first rebases WAVE_BASE itself: create a temporary
branch at OLD_WAVE_BASE and rebase it once onto the new main; its rebased tip
is NEW_WAVE_BASE. Then move each wave branch inside its executor's existing
worktree — the same `-C <worktree-path>` targeting Phase 7 uses. Quiesce the
executor first, then run
`git -C <worktree-path> rebase --onto NEW_WAVE_BASE OLD_WAVE_BASE` in that
worktree, where the branch is already HEAD: no `<branch>` argument and no
checkout (a `<branch>`-argument rebase from the orchestrator checkout fails
with "already used by worktree"). The rebase replays only the branch's own
commits, so the shared annotation commits replay exactly
once, never per-branch, and every branch carries the same objects. Push each
rewritten branch with `git push --force-with-lease`, explicitly authorized for
this rewrite of pushed branch SHAs. WAVE_BASE moves to NEW_WAVE_BASE.

**Refresh**: the Phase 4 recording is only the initial value. When a Phase 5.0
coordination PR lands, or Wave N merges, re-record WAVE_BASE from the merged
main tip before the next wave's branches fork.

For each wave, launch agents with `isolation: "worktree"` — the **coder
profile** (`agents/coder.md`, whose contract is `profiles/coder/PROFILE.md`;
frontmatter pins `model: strong` per § Model policy — coding workers).

The execute-agent contract's FIRST action is mechanical. The agent invokes the
hunt skill with the ticket ID:

```
Skill(skill: "hunt", args: "<id>")
```

It then follows the contract the skill loader returns. The agent prompt must NOT
paraphrase, summarize, or inline hunt's steps; the versioned `skills/hunt/SKILL.md`
is the single live execution contract, and the loader supplies it fresh on every
run. (A prose paraphrase is exactly what drifted between the aedist Wave A and
Wave B prompts, 2026-06-11/12: the contract lived in prompt-writing memory
instead of the skill.) The agent pushes its branch and opens a merge request as
hunt's flow dictates.

Wait for wave to complete.

## Phase 6: Verify (per-ticket `/gaze`)

Mood: Be strict, skeptical, nit-picky, detail-oriented. Aim for code excellence and integrity.

**Per-ticket:** run `/gaze` on every merge request — the orchestrator itself
runs it inline, one per PR (an inline run is serial; only the detached shape
below adds concurrency, and disjoint-file PRs may run concurrently through
it). Verify file-sharing PRs sequentially to avoid concurrent-fix collisions.
Respect the max-concurrent-agents cap (see `rules/claude-code.md` § Subagent
levers). When the runtime's nesting blocks the inline run — a raid is itself
an agent orchestration, and child sessions do not inherit the agent connector
(PRs #1060/#1061, #1129-#1132; ticket 1017); detect it by the inline run
reporting `battery: NOT-RUN — cause: no-agent-tool`, `depth`, or `guard`,
or by a known absent agent connector — substitute one detached, headless, non-interactive
CLI session per PR per the detached-seat contract
(`skills/review-pr/SKILL.md` § Detached-seat substitution, ticket 1017): cwd
pinned to the PR's worktree, prompt embedding `/gaze <pr-number>` plus the
caller prerequisites and the containment rails (no merges, no writes outside
the PR branch); the result is observed by polling the written verdict
artifact — the `## /verify-gate verdict` PR comment per the output shape of
`skills/gaze/SKILL.md`, accepted only when its `ruled_tip_sha` matches the
branch tip — under that contract's bounded wait, never a spawn exit status,
and the structured verdict must return to the orchestrator. A REROLL
bump/fix runs in the PR's worktree so its commits land on the PR branch,
never on main mid-wave. Phase 7 merges stay strictly sequential.

**Per-wave:** after all per-ticket `/gaze` runs complete, launch one integration-review
subagent (read-only; mid-tier worker per § Model policy) to check:
- Do the merged/merge-pending PRs compose without contradiction?
- Does `make check` still pass if we imagine them all merged?
- Are there testing gaps visible only at wave granularity (e.g., two PRs touching the
  same test file in incompatible ways)?
- Run `git merge-tree --write-tree <headA> <headB>` pairwise on the wave's PR
  head refs (it takes no path filter). A conflicted path under `tickets/` means
  divergent annotation copies — a WAVE_BASE violation — even when the
  conflicting lines carry identical prose; conflicts elsewhere are ordinary.

Wave-level findings go to the human as a wave-summary comment; they do not block
individual `/gaze` verdicts.

## Phase 7: Merge (sequential per-wave)

**Token economy rule**: Any time a ticket must be created in any phase, create it
with `tickets/erg new "<title>"` — never write the file directly or compute the
next ID manually. `erg new` allocates the next free ID and writes a valid
`%erg 0.1` file (preamble + `created` log line + empty body) race-safely; fill
the body, then `erg validate tickets/<new-file>.erg` (file arg, not directory)
and `erg check tickets/`, keeping mechanical work inside the tool where it belongs.

**Bundle follow-up tickets into the spawning PR.** When a raid or review
surfaces a follow-up, create it via `tickets/erg new` and commit the `.erg` onto the
current PR branch — the ticket only, never the fix. Reference it from the PR
body (`Related follow-up: tickets/NNNN`, or `Scope overflow: tickets/NNNN` when
it comes from a verify-gate verdict). The PR's `**Ticket:**` line still closes
only its own ticket on merge; the bundled follow-up stays open. Never file the
follow-up on a main checkout — main is read-only and may be dirty with parallel
work.

For each wave, merge APPROVED PRs one at a time. A PR is merge-eligible if:
- `/verify-gate` verdict is APPROVED (one REROLL allowed — Phase 6 handles this), AND
- `scope_overflow` in the verdict is empty or all entries have suggested disposition
  TICKETED (caller creates tickets via `tickets/erg new` and adds `Scope overflow:
  tickets/NNNN` to the PR body before merging).

Any ESCALATE verdict (from exit criteria, review comments, or scope overflow) stops
the PR — it stays open for human review.

This phase runs immediately after the execute/verify forks return, so the shell
cwd may sit in a foreign worktree. Before the first branch-mutating git below,
confirm the tree: `git rev-parse --show-toplevel` must equal the session worktree
(rules/git.md § anchor across a forked-skill boundary).

For each eligible PR, sequentially within the wave:
1. `git fetch origin` to pick up any prior merges.
2. No checkout needed — `-C <path>` points the merge tool at a checkout that
   already has the PR branch. An Execute agent's own worktree qualifies
   directly: take its path from the agent's completion notification
   (`.claude/worktrees/agent-<id>`). Do not check out, `cd`, or `EnterWorktree`
   into it, and do not delete and re-checkout the branch. <!-- harness-extension-point -->
3. Check PR is still mergeable (no conflicts from earlier merges in this wave).
4. Run `"$IDH_ROOT/skills/merge/erg-pr-merge" -C <worktree-path> <pr-number>`.
   This atomically closes the ticket and merges via GitHub API.
   <!-- harness-extension-point -->
   Runtime permission rules must authorize the resolved helper path. Use
   `-C` to select the worktree for every Git and forge operation.
5. If merge fails (conflict, CI regression), ESCALATE — leave a PR comment and move to the next PR.
   A *permission denial* on the merge call is not a merge failure — handle it
   per § Merge-permission denial below, not by ESCALATE.

### Merge-permission denial: cure the objection with evidence

The permission layer may decline an APPROVED PR's merge because the review
is insufficiently independent of its author. Inspect the stated objection
and the actual producer/reviewer identities; do not assume that a launched
reviewer supplied independent evidence. Never weaken permissions, skip checks
or hand-merge around the guard.

1. Do not retry the denied call verbatim.
2. Request independent review of the current PR head through the active
   runtime, using `skills/reviewers/SKILL.md` and its live-route reference.
   Describe the expertise, capability and independence needed to answer the
   objection. Let the runtime discover and route a suitable reviewer; record
   the actual identity, route, independence basis, reviewed base/head and
   completed report. Disposition every returned finding through verify-gate;
   a blocking finding sends the PR back through Phase 6. If fixes change the
   head, refresh the independent evidence before retrying. Preserve failed or
   missing review records and `PANEL-INTEGRITY:` verbatim in the external
   verdict record; they are coverage limitations, not findings to disposition.
3. Only when completed independent evidence answers the stated objection and
   findings have a clean disposition, post that evidence and its disposition
   on the PR. Quote the verdict and this recovery contract in the transcript
   and retry the merge once. A claimed route or empty response is insufficient.
4. If independent evidence is unavailable or insufficient, or the retry is
   denied, park the PR merge-ready, continue the wave, and name each parked
   PR, the unresolved objection and deferred post-merge steps (cleanup +
   per-PR roar) in the briefing. Optional external review's fail-open policy
   does not waive a merge denial; do not bypass the permission layer.

After all waves, in one compound so the `cd` persists across the rebase:
`cd <session-worktree> && git checkout main && git pull --rebase origin main`, then
`make check`. New failures → revert last merge + ticket.

## Phase 8: Celebrate (per-merged-PR)

After all merges, from the updated main branch, run `/roar` for each
successfully merged PR. The roar pre-check (`git merge-base --is-ancestor
HEAD origin/main`) passes because HEAD is main after the pull.

## Mid-session checkpoint (~50% effort)

- [ ] Opened at least one north-star-forward merge request?
- [ ] Tooling/deliverable ratio within bounds? (N/A for a tooling/library project — the harness IS the deliverable; see § Balance rule)
- [ ] Self-reviewed at least one merge request?
- [ ] `make check` passes on main?

Autonomous mode: ralph loop to next wave.

## Wrap up

1. `make check` on main — compare against baseline. New failures → ticket.
1b. Scan ticket log sections for current bump notes and legacy bump entries;
    print counts by ticket and category (author names may contain spaces):
    ```bash
    awk '
      FNR == 1 { in_log = 0; in_body = 0 }
      in_body { next }
      /^--- log ---$/ { in_log = 1; next }
      /^--- body ---$/ { in_log = 0; in_body = 1; next }
      in_log && /^[0-9][0-9][0-9][0-9]-/ {
        if (match($0, / (bump|note) /)) {
          split(substr($0, RSTART + 1), fields, " ")
          if (fields[1] == "note" && fields[2] == "bump" &&
              fields[3] == "verify-reroll") fields[2] = fields[3]
          if (fields[1] == "note" && fields[2] != "verify-reroll" &&
              fields[2] != "circuit-breaker") next
          ticket = FILENAME
          sub(/^.*\//, "", ticket)
          ticket = substr(ticket, 1, 4)
          count[ticket " " fields[2]]++
        }
      }
      END {
        for (key in count) {
          split(key, fields, " ")
          printf "Ticket %s: %d %s\n", fields[1], count[key], fields[2]
        }
      }
    ' tickets/*.erg tickets/closed/*.erg | sort
    ```
    Combine category rows in the briefing as:
    `Ticket NNNN: N bumps (X permission, Y verify-reroll, …) → Z% trivial`.
2. All merged PRs confirmed on main. Any ESCALATED PRs listed with reasons.
   Any ticket Phase 1 excluded as skip-labelled is listed here too, with the
   decisions it is waiting on. When the queue held nothing else, that list is
   the run's deliverable, not evidence of an idle run.
3. Write briefing (session log + merge request list + test delta).
4. Do NOT run `/lair`.

## Circuit breakers

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
the order, so keep it: salvage first, then `git worktree remove` (never
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
`/hunt` runs the gate through `raid-gate.py`, whose short-lived heartbeat is
keyed to this worktree. Another session's gate cannot excuse this executor,
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

**Ping-pong detector**: If two agents edit the same file on the
same branch, STOP. Reset to last known-good commit, relaunch ONE agent.
Bump reason: `ping-pong on {file}`.

**Redirect ban**: Do not use SendMessage to redirect a running
agent. Kill and relaunch with corrected instructions.
Bump reason: `redirect ban triggered`.

**Escalation**: If the same fix fails twice, stop and leave a
ticket comment with the two failed approaches.

## Worker models

Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); never rely on the session model by default. Seats that
must be independent follow `skills/route/references/decorrelation.md`.
