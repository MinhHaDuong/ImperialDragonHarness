---
metadata:
  category: build
  order: 7
name: raid
description: "Work through multiple tickets autonomously: pick targets, implement each in isolated worktree waves, verify, and merge APPROVED PRs after verify-gate clears."
disable-model-invocation: false
user-invocable: true
argument-hint: '[ticket-ids or "all open"]'
---

Orchestration with ordinary judgment; choose workers per the `route` skill (`skills/route/SKILL.md`).

# Raid $ARGUMENTS — Imperial Dragon hunt

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

A raid does not redefine skills. It loads the hunt,
gaze and roar skills, among others. Its job is sequencing, wave management,
and enforcing invariants.

## Model policy

Name a role for every launch, state the choice and why. Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); seats that must be independent follow
`skills/route/references/decorrelation.md` ("The launch line"). Skill frontmatter
does not configure spawned children.

- **Execute:** the coder profile (`agents/coder.md`); cheaper workers for
  bounded tasks.
- **Advisor:** an advisor model as a one-shot call with a
  self-contained brief on a deep, well-defined problem: a ticket that can be
  neither done nor split, a review of a scientific argument, a design review of
  a critical feature. Never a standing setting of the orchestrator or a
  fan-out member.
- **Per-ticket gaze and verify-gate:** follow their own launch choices.

## Balance rule

**Deliverable work ≥60%, tooling ≤40%.** If two consecutive tickets were tooling, the next must advance a deliverable. Track in session log.

**Deliverables**: whatever the project's north star names as its product. For a *science* project that's papers, slides, reading notes, figures, responses to reviewers — and tooling (tests, hygiene, refactoring) is the supporting infrastructure the rule throttles. For a *tooling/library* project (e.g. this harness, git-erg) the product **is** the skills, rules, tests, and helpers — that work is the deliverable, not the throttled category, and the ratio does not apply. Read "deliverable" off `STATE.md`'s north star, never off a fixed papers/slides list.

**Escape hatch**: if `make check-fast` fails and blocks all deliverable work, tooling may exceed 40%. Document why.

## Checkpointing

Every phase ends with a git commit. If the session dies, resume by
reading the ticket logs and git history to determine which phase
completed last. The checkpoint is the repo, not session state.

## Phase 1: Select

At raid start, before selecting, write `RAID_START` and arm the sitrep cadence
as `## Sitrep cadence` below describes.

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
it is waiting on, and count that as a success outcome — the same standing hunt's
Plan phase gives a decision escalated to the author.

**Carve-out: an explicit `/raid <id>` runs.** The exclusion governs target
*discovery* (the "all open" path), never a ticket named by ID. A named ticket
is a caller's deliberate choice, so it executes; note the override in the
briefing so the choice is visible.

Do not read that carve-out as "explicit means the author asked." The
explicit-ID shape covers an author typing it and a program building it alike,
and this skill cannot tell them apart. The autonomous caller that used to exist
was safe for a reason that lived upstream of here, not in this phase: its
candidates came from `erg ready`, which already applies the skip filter. That
caller no longer exists, so there is none today — and any future one that synthesizes IDs some other way needs its own
screen before it reaches this carve-out.

If EVERY discovered ticket is skip-labelled, the run ends with that wrap-up
briefing (each ticket and the decisions it waits on) rather than an
empty-run report. One question round the author can answer in a single pass
is the deliverable.

Apply the monster-ticket checklist (`rules/workflow.md` § Ticket discipline for multi-PR work) to each candidate before wave grouping; decompose monsters into tracking + child tickets rather than holding them or fanning them into a colliding wave.

## Phase 2: Imagine (parallel)

For each ticket, launch an agent (background, no isolation needed — read-only;
worker chosen per § Model policy):
- Read ticket + STATE.md + surrounding code
- Reimagine: why now, why this scope, what's the simplest path
- **Antipattern scan (scope).** YAGNI (search the package registry —
  don't hand-roll what a library already does), premature abstraction.
  Annotate any hits with the proposed fix.

Wait for all.

### Blind-Spot pass (cross-ticket)

Before committing the reimagined tickets, launch **one** additional read-only
agent (worker chosen per § Model policy) over the original tickets **and all
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

For each reimagined ticket, launch an agent (background; worker chosen per
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
existence checks — paths/lines/signatures; a stronger worker for the cross-ticket
conflict and cross-cutting-registry scan, which is judgement across N plans, not
lookup — missing it cost a resurrection agent for 3 of 4 merges, see § Phase 5.0
below):
- File paths, line numbers, function signatures
- Data assumptions, API key requirements
- Cross-ticket conflicts
- Cross-cutting registries: a file holding a shared hash-set / dict / dispatch
  table (test allowlist, dispatch keys, config conventions) that 3+ PRs will
  edit. Flag any you find — they trigger the Phase 5.0 coordination PR.

Annotate tickets with PASS/WARN/BLOCK. Commit annotations.

After committing the final annotation, run `git pull --rebase origin main`, then
record `WAVE_BASE="$(git rev-parse HEAD)"` in the raid log (fixed path and format: `## Sitrep cadence`). Per-phase annotation
commits stay as they are — WAVE_BASE is simply their last commit — so every wave
ticket annotation is an ancestor of it and all wave branches fork from one
shared, mergeable base. Patch-equivalent commits are not merge-equivalent: a
raid that carried the same annotation patch natively and by cherry-pick saw every
pair of wave PRs holding different SHAs of that one patch collide on the ticket
files at merge time.

## Phase 5.0: Land coordination PR (cross-cutting registries)

Only when 3+ PRs in a wave will edit one file holding a shared registry;
otherwise skip. When, why and how: `references/coordination-pr.md`.

<!-- inline: references/coordination-pr.md -->

## Phase 5: Execute (waves, worktree-isolated)

Group tickets into waves:
- Wave N: no unmerged dependencies
- Wave N+1: depends on Wave N results

**Wave base**: every wave branch forks from WAVE_BASE exactly — executors
spawn from the main checkout sitting at WAVE_BASE (Phase 4), never from
whatever origin/main has drifted to since.

**Mid-wave advance**: when origin/main advances after executors have forked,
rebase WAVE_BASE once and move every wave branch onto it, per
`references/wave-rebase.md`.

<!-- inline: references/wave-rebase.md -->

**Refresh**: the Phase 4 recording is only the initial value. When a Phase 5.0
coordination PR lands, or Wave N merges, re-record WAVE_BASE from the merged
main tip before the next wave's branches fork.

For each wave, launch agents — each creates and locks its own worktree (`skills/hunt/SKILL.md` § Worktree) — the **coder
profile** (`agents/coder.md`, whose contract is `profiles/coder/PROFILE.md`;
the model is chosen per launch from the `route` skill, no frontmatter pin).

The execute-agent contract's FIRST action is mechanical: the agent loads the
hunt skill with `<id> inline` as its argument. It then follows the contract the skill loader returns. The agent prompt must NOT
paraphrase, summarize, or inline hunt's phases; the versioned `skills/hunt/SKILL.md`
is the single live execution contract, and the loader supplies it fresh on every
run. (A prose paraphrase drifts: the contract then lives in prompt-writing memory
instead of the skill.) The agent lands its branch as hunt's Verify phase
dictates: a merge request on a forge, a ready-to-merge branch without one. An agent that returns its ticket as a likely monster
brings a proposed decomposition instead: apply the monster checklist to it,
file the split, and schedule the children in a later wave. A partial branch it
pushed is named in the split for the child that inherits it; its unlocked
worktree is removed with the wave's. No later wave left: report the split to
the author instead.

Wait for wave to complete.

**Attribution lines.** Only the orchestrator records the writer lines; seats
return their identity and never write attribution. Once a wave unit exists,
record the `writer: step=plan` and `writer: step=execute` lines (identity as
the seats reported it, effort `not-stated` unless set at launch) on the unit's
review on notes, locally, with no network call (ticket 1307):
`python3 "$IDH_ROOT/scripts/attribution_record.py" --record-writer '<line>' --unit pr:<n>`
(no forge: `--unit branch:<name>`). A non-zero exit is a visible capture
failure, not a silent skip. Nothing edits the PR body before landing, which
renders the block from notes (`raid_land.py`).
Line fields and order: `skills/merge/references/claims.md` § Line formats; a
`writer:` line may be recorded after the review's answers.

## Phase 6: Verify (per-ticket gaze, then verify-gate)

Mood: Be strict, skeptical, nit-picky, detail-oriented. Aim for code excellence and integrity.

**Tier first** (`skills/merge/SKILL.md` § Gating tiers, the one home): a
bookkeeping-tier merge request skips gaze and verify-gate and goes to
Phase 7 on its mechanical checks. Everything below is the full tier.

**Per-ticket:** ensure a REVIEWED gaze record on the branch tip, then run
the verify-gate skill on the head it reviewed. Hunt's Verify phase already ran gaze and
fixed its findings, so the raid reads that record first (the review's latest
answer on notes, `review_notes.py answers --unit pr:<n> --latest --json`) and re-runs gaze
only when it is missing, ESCALATE, or stale against the tip
(`skills/merge/SKILL.md` § Gating tiers, which also counts a `seats:
self-only` record as missing); a second review of a head gaze
already reviewed buys nothing and costs a full gaze run. Gaze reviews and
never returns APPROVED; the gate rules APPROVED / REROLL / ESCALATE /
NEEDS-AUTHOR. The orchestrator itself
runs them inline, one per PR (an inline run is serial; only the detached shape
below adds concurrency, and disjoint-file PRs may run concurrently through
it). Verify file-sharing PRs sequentially to avoid concurrent-fix collisions.
Respect the max-concurrent-agents cap (see `rules/claude-code.md` § Subagent
levers).
When the runtime's nesting blocks the inline run, substitute one detached
session per PR as `references/detached-gaze.md` prescribes: its trigger,
launch shape and result acceptance.

<!-- inline: references/detached-gaze.md -->

A gaze result of ESCALATE, or no accepted result (missing at the end of the
bounded wait, or its `reviewed_head_sha` stale against the branch tip), means
the gate is not run: the review never completed, and the PR follows
`rules/workflow.md` § Escalation protocol.
A run that returns no result is handled as `references/detached-gaze.md` § No result says.
Stale means the tip adds more than a bookkeeping delta to `reviewed_head_sha`
(`skills/merge/SKILL.md` § Gating tiers), judged before the raid adds the fix
for a gate's round-1 REROLL, which does not void the result (the round-2
re-gate rules the fix). A FINDINGS fix does: it moves the head past what gaze
reviewed. On FINDINGS the fix agent fixes the listed items and the raid runs
gaze on the new head with a new, narrower intent naming those fixes, before
any gate: a head gaze did not review is never gated. The raid states each
intent it passes (gaze with `<pr> verify <what> because <why>`); with none, gaze
reviews the whole merge request against its ticket's exit criteria.
Only on a gaze result of REVIEWED run
verify-gate with `<pr-number> repo=<PR's worktree> session=<uuid>` the same way (gaze has removed
its review tree by then; the gate checks out the PR head in a worktree of its
own and removes it, while the raid keeps the PR's worktree until gating ends);
its verdict is accepted only when the branch tip adds at most a bookkeeping
delta to its `ruled_tip_sha` (§ Gating tiers). On `FINDINGS` or
a REROLL, a coder fixes the listed items in the PR's worktree so its commits
land on the PR branch, never on main mid-wave, and the REROLL bump is posed per
`skills/verify-gate/SKILL.md`; the gate allows two rounds, a third escalates.
Before the round-1 gate the raid closes the PR's ticket on the PR branch
(`skills/merge/SKILL.md` § close the ticket on the branch before gating), so the
gate rules the head that will merge.
The raid owns each PR's gate session (`skills/verify-gate/SKILL.md` § Gate
sessions): it generates one UUID per PR before round 1, passes the same
`session=` to round 1 and to the single re-gate after the fix, and never runs
the gate a third time or opens a second session for the PR. A round-2 REROLL
is ESCALATE; ESCALATE follows `rules/workflow.md` § Escalation protocol, which may fix,
re-ticket or park the PR but never merges past the gate (that call is the
author's, `skills/verify-gate/SKILL.md`); NEEDS-AUTHOR waits for the author. The same two-round
budget binds the merge-permission-denial recovery (§ Merge-permission denial):
once two gate rounds are posted on the PR, that recovery parks the PR and
escalates to the author instead of sending it back through Phase 6.

**No forge.** A repository with no `origin` remote runs Phases 6-7 on notes
and the local gated merge (flow F2, `conception/2026-10-27-review-merge-flows.md`),
the same steps through the helpers, never raw git: the request is
`review_notes.py open --branch <branch> --base-ref <base>`; gaze takes
`branch:<branch>` and its `answer` entry is what `review_notes.py coverage|gate <id> HEAD`
reads; verify-gate rules through `gate` and appends its ruling with `verdict`
(`skills/verify-gate/SKILL.md`). With `origin` and no `gh`, nothing lands: the PR
waits (`raid_land.py` refuses, exit 1), the local merge is never the fallback.

**Fix-and-regate.** On `FINDINGS` or a round-1 REROLL, follow
`references/fix-and-regate.md`: the fix agent's rules, the re-review or
re-gate, and the loop's breakers.

<!-- inline: references/fix-and-regate.md -->

Phase 7 merges stay strictly sequential.

**Per-wave:** after all per-ticket gaze runs complete, launch one integration-review
subagent (read-only; worker chosen per § Model policy) to check:
- Do the merged/merge-pending PRs compose without contradiction?
- Does `make check` still pass if we imagine them all merged?
- Are there testing gaps visible only at wave granularity (e.g., two PRs touching the
  same test file in incompatible ways)?
- Run `git merge-tree --write-tree <headA> <headB>` pairwise on the wave's PR
  head refs (it takes no path filter). A conflicted path under `tickets/` means
  divergent annotation copies — a WAVE_BASE violation — even when the
  conflicting lines carry identical prose; conflicts elsewhere are ordinary.

Wave-level findings go to the human as a wave-summary comment; they do not block
individual gaze results and verify-gate verdicts.

## Phase 7: Merge (sequential per-wave)

**Creating a ticket** in any phase, or bundling a follow-up that a raid or
review surfaced: `references/follow-up-tickets.md`.

<!-- inline: references/follow-up-tickets.md -->

For each wave, merge APPROVED PRs one at a time. A PR is merge-eligible if:
- the merge request is bookkeeping tier (`skills/merge/SKILL.md` § Gating tiers), or its
  verify-gate verdict is APPROVED (one REROLL allowed — Phase 6 handles this), AND
- `scope_overflow` in the verdict is empty or all entries have suggested disposition
  TICKETED (caller creates tickets via `tickets/erg new` and adds `Scope overflow:
  tickets/NNNN` to the PR body before merging).

Any ESCALATE verdict (from exit criteria, review comments, or scope overflow) stops
the PR: it stays open and follows `rules/workflow.md` § Escalation protocol.

A `NEEDS-AUTHOR` verdict is
not merge-eligible without the author: surface it to the author and leave the PR open.
The raid never merges it on its own authority.

This phase runs immediately after the execute/verify forks return, so the shell
cwd may sit in a foreign worktree. Before the first branch-mutating git below,
confirm the tree: `git rev-parse --show-toplevel` must equal the session worktree
(rules/git.md § anchor across a forked-skill boundary).

For each eligible PR, sequentially within the wave:
1. `git fetch origin` to pick up any prior merges.
2. Run the recipe's commands inside the PR's own worktree, as one command
   (`(cd <worktree-path> && ...)`, a subshell); `git -C <worktree-path>` is
   for single reads. An Execute agent's own worktree qualifies
   directly: take its path from the agent's completion notification; a path equal to the
   session worktree is refused, never merged or cleaned up from. Never check the
   branch out anywhere else, and do not delete and re-checkout the branch.
3. Check PR is still mergeable (no conflicts from earlier merges in this wave).
4. Merge by the recipe, `skills/merge/SKILL.md` § The recipe, in one call from the PR's
   worktree: `python3 "$IDH_ROOT/scripts/raid_land.py" <pr> --ruled-head <ruled_tip_sha|-> --ruled-claims <ids,|-> --cleanup`
   (`--ruled-claims` is the ruled verdict's `ticket:` field, never a fresh read of the body)
   (close, head pin, record with one re-record, disarm, pinned merge, read-back, sync, a
   `<pr> merge <start> <end>` row for `step_clock.py`). Exit 1 refused, 4 merged but main
   unsynced (report, never re-merge), 5 queued, 6 merge outcome unknown (read the request, never
   re-merge). The after-merge runner (recipe step 9) is started by the main-update hook on the sync. The checks below are what `raid_land.py` enforces,
   by the recipe,
   only after `git fetch origin`, then `git rev-parse HEAD` == `git rev-parse origin/<branch>`
   (HEAD read with `-C <worktree-path>`) and, full tier, a head that adds at
   most a bookkeeping delta to the gate's `ruled_tip_sha` (`skills/merge/SKILL.md`
   § Gating tiers); otherwise no merge. Close before gating: Phase 6 closed the ticket on
   the branch before the round-1 gate, so the recipe's close step finds it in
   `tickets/closed/` and adds no close commit.
   **Gated base** (`.merge-gate.json` on the base, `skills/merge/SKILL.md`
   § Gated base): the record check, the record run when it is missing, the
   pinned merge and the read-back run as one background command. The record
   is the gate; the read-back is the outcome (MERGED at the gated head).
   A missing record after an earlier merge in the wave moved the base means
   record again on the same head: mechanical, it spends no gate round. A
   second miss goes in the briefing.
   **Ungated base:** the merge may be queued, not landed: pending checks are normal.
   Pending is not a
   failure: wait as `skills/merge/SKILL.md` § Waiting for a queued merge
   prescribes (one bounded background command) and move on to the next PR
   meanwhile; a PR still pending when that wait ends is listed as queued in the
   briefing, not as merged.
   **No forge:** the call is the same with `<pr>` = `branch:<branch> [base=<ref>]`. It is a
   `--no-ff` merge pinned by head OID, the base moved under the main-update guard, the gate record
   in this repository's `refs/notes/gate`; nothing is pushed (no `origin`), and the repository's own
   main is canonical. Step 1 and the `origin/<branch>` head equality below do not apply (there is no
   `origin`); `raid_land.py` checks the head against the ruled tip locally. Claimed tickets must be closed on the branch beforehand; the read-back is the
   `MERGED <oid> -` that `raid_land.py` reads back.
5. If merge fails (conflict, CI regression), or the read-back is CLOSED, or OPEN on a gated base, or unreadable, ESCALATE (an OPEN queued merge on an ungated base is pending, step 4) — leave a PR comment and move to the next PR.
   A *permission denial* on the merge call is not a merge failure — handle it
   per § Merge-permission denial below, not by ESCALATE.

### Merge-permission denial: cure the objection with evidence

Read `references/merge-permission-denial.md` when the permission layer
declines an APPROVED PR's merge.

<!-- inline: references/merge-permission-denial.md -->

After all waves, in one compound so the `cd` persists across the sync:
`cd <session-worktree> && "$IDH_ROOT/scripts/sync-local-main.sh" . main`. The
sync script always exits 0 and leaves a diverged main untouched: read its
output, and stop if a line says `left untouched`, `diverged` or `skipped`.
A red on main is reported and ticketed, never reverted (`rules/workflow.md`
§ Trust, Verify, Monitor; on a gated base, `skills/merge/SKILL.md` step 9). Gated base: the after-merge runner the sync started covers the tip
and opens the ticket; read its log, never wait on it. Ungated base: `make check`
in a checkout of the synced main (the primary checkout, or a throwaway
`git worktree add --detach <dir> main`); new failures → ticket.

## Phase 8: Celebrate (per-merged-PR)

After all merges, from the updated main branch, load the roar skill for each
PR whose read-back answered MERGED; a pending PR gets its
roar when its bounded wait (`skills/merge/SKILL.md` § Waiting for a queued
merge) reports it merged. The roar pre-check (`git merge-base --is-ancestor
HEAD origin/main`) passes because HEAD is main after the pull.

## Mid-session checkpoint (~50% effort)

- [ ] Opened at least one north-star-forward merge request?
- [ ] Tooling/deliverable ratio within bounds? (N/A for a tooling/library project — the harness IS the deliverable; see § Balance rule)
- [ ] Self-reviewed at least one merge request?
- [ ] `make check` passes on main?

Autonomous mode: ralph loop to next wave.

## Sitrep cadence

The raid log has a fixed path and format (`references/sitrep.md`); append
`RAID_START`, `WAVE_BASE`, `WAVE`, `PR` (each step change), `BREAKER` and `QUEUE` lines with
`python3 "$IDH_ROOT/scripts/raid_log.py" append EVENT raid=<id> key=value ...`.
`RAID_START` mints the id and prints it: read it there and put `raid=<id>` on
every later append and on the sitrep command. At raid
start, after `RAID_START`, run `python3 "$IDH_ROOT/scripts/raid-sitrep.py" --raid <id>`
once and arm the cadence:
`python3 "$IDH_ROOT/scripts/runtime.py" wake arm --after 900 --cmd "python3 '$IDH_ROOT/scripts/raid-sitrep.py' --raid <id>"`
(answers read as in `references/sitrep.md` § Wake sources; on `NOOP`, run the sitrep at each wave boundary and breaker event, and say so).
On each wake, read the sitrep, re-arm, and act on its last line: `NEXT resume
wave` means launch the next wave now rather than ending the turn; `NEXT
wrap-up` means proceed to Wrap up; `UNREADABLE` (exit 2) means repair the log
or the failing read first.

<!-- inline: references/sitrep.md -->

## Wrap up

1. Main against baseline: on a gated base, the after-merge log of the newest
   tip (§ Phase 7), whose runner opens the ticket itself; on an ungated base,
   `make check` on main, new failures → ticket.
1b. Scan ticket log sections for current bump notes and legacy bump entries;
    print counts by ticket and category (author names may contain spaces):
    ```bash
    IDH_ROOT="${IDH_ROOT:?set IDH_ROOT per the helper-command note at the top}"
    python3 "$IDH_ROOT/scripts/raid-reroll-tally.py" tickets tickets/closed
    ```
    A `WARNING drift:` line on stderr means a ticket log has lines outside the
    timestamp shape, a ticket has no `--- log ---` marker, or entries exist but
    none is a bump or note (verb rename); uncounted entries are not zeros. Exit 2
    on stderr (`no ticket directory`, `cannot read ...`) means part of the repo
    could not be read: report it, do not read the rows as an all-clear.
    Combine category rows in the briefing as:
    `Ticket NNNN: N entries (X permission, Y verify-reroll, Z circuit-breaker, …)`.
2. All merged PRs confirmed on main. Any ESCALATED PRs listed with reasons.
   Any ticket Phase 1 excluded as skip-labelled is listed here too, with the
   decisions it is waiting on. When the queue held nothing else, that list is
   the run's deliverable, not evidence of an idle run.
3. Write briefing (session log + merge request list + test delta). Add the
   timing table: for each merge request, note `<pr> <step> <start> <end>` rows
   (epoch seconds from `step_clock.py start`, read by the raid itself before and after each call, since gate and merge print only durations: gaze, each gate round, merge) as
   the steps run, and print `python3 "$IDH_ROOT/scripts/step_clock.py" table`
   with the rows on stdin: per-step durations, the total from first gaze to MERGED, and the
   slowest step. A step with no clock reading is listed as `not measured`.
4. Disarm the sitrep cadence after the last sitrep: `python3 "$IDH_ROOT/scripts/runtime.py" wake disarm`; its `NOOP` names what to stop yourself (on Claude Code, the pending background command).
5. Do NOT run the lair skill.

## Circuit breakers

Read `references/circuit-breakers.md` before killing or relaunching an
agent, when an executor may have stalled or timed out, when two agents edit
one file on one branch, before redirecting a running agent, and when the
same fix fails twice. From the first launch, record the time of each push
and each observed change in each executor's worktree: the stall check needs
them.

<!-- inline: references/circuit-breakers.md -->
