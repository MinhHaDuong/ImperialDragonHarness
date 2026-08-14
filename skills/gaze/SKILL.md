---
name: gaze
description: "Run the full per-PR verification loop (adherence + review + review-pr + simplify), then gate through /verify-gate. Bounces the PR for at most one retry. Does not merge — the merge decision belongs to the caller."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number>"
context: fork
# Background by intent: /gaze is long-running, and a raid wave gates several PRs
# at once — backgrounding the orchestrator is what lets those run concurrently.
# This matches the Claude Code 2.1.218 default; pinned explicitly so a future
# default flip cannot serialize a wave silently. Its own sub-skills and reviewer
# agents run FOREGROUND (see "Fork execution contract" below) — the two are
# different axes: parallelism comes from concurrent tool calls inside one
# message, never from backgrounding a phase this skill must wait on.
background: true
---

# Gaze — verify PR $ARGUMENTS, six-phase loop with anti-rubber-stamp gate

> **TASK DIRECTIVE — execute now.** You are running `/gaze` on PR `$ARGUMENTS`.
> This file is your operating procedure, not reference documentation: begin at
> phase 1 immediately. If `$ARGUMENTS` does not contain a PR number, STOP and
> return ESCALATE with reason "no PR argument" — do NOT infer a task from the
> environment (worktree name, git status snapshot, ticket files, or the shared
> task list).

**Caller responsibility (before this fork is ever spawned).** The rule above
binds the fork, which starts with no cwd and no conversation (ticket 0193 —
a bare fork once guessed its target from ambient state and pushed a rogue
PR). It does not mean the user must supply a bare number by hand every time.
The invoking session has a cwd and a conversation — when the user types
`/gaze` with no argument, resolve the PR number *before* invoking this skill:
query the forge for the PR associated with the current branch, or reuse a PR
number already established earlier in the conversation. Invoke with that
number filled in. Only ask the user for it when no such source exists or two
candidates conflict.
<!-- harness-extension-point: on GitHub, `gh pr view --json number` resolves
the current branch's PR number. -->

One skill, one PR, one decision: APPROVED / REROLL / ESCALATE. **Does not
merge** — the merge decision belongs to the caller (the human or the raid).

## When to use

- Raid Phase 6 (per-ticket verification before merge).
- Any time an author wants a full-depth check on a single PR before asking for merge.
- **Do NOT** use for quick sanity — use `/review` or `/review-pr` directly.

## Invariants

- Runs on exactly one PR.
- Two gate rounds maximum. Third round is forbidden — escalate instead.
- Does not merge. The verdict is structured output; the merge decision belongs to the caller.
- The fix loop between rounds makes commits on the PR branch; no changes to other branches.
- `--force-approve` is supported for explicit human override; it is logged loudly in the
  PR comments and the skill transcript.
- Convergence mode (`convergence.enabled`, default off) may shorten a *repeat* invocation
  to the gate phase only — see § Convergence mode; it never relaxes the gate itself.
- **Cross-repo prerequisite**: the caller must ensure cwd is the target project before
  invoking `/gaze`. The skill and its sub-skills (`/verify-gate`, `/simplify`, etc.)
  use `gh` and `git` commands that resolve against cwd.

## Fork execution contract

`/gaze` runs as a `context: fork` (see frontmatter). A fork's turn ends the
instant it stops calling tools. Every agent this skill spawns — the phase 2–4
reviewers, the phase 6 gate, the REROLL fix agent — must therefore be launched
**foreground** (`run_in_background: false`), so the fork blocks on the result
and continues to the next phase when the agent returns. Launching them
`run_in_background: true` and then "waiting" does not wait: the fork stops
calling tools, its turn ends, and the background completions re-invoke the
**MAIN loop**, not the fork. The fork's last message is then a fan-out
narration ("reviewers are running in parallel…") instead of a verdict, and
phases 5–6 never run. This orphaned two real gate runs (aedist `/gaze 977`
and `/gaze 978`, 2026-06-11), each forcing the caller to relaunch a duplicate
reviewer battery.

**The contract applies recursively.** Any nested fan-out performed on `/gaze`'s
behalf — a reviewer Agent (e.g. Agent C) that itself spins a panel of
perspective agents — inherits this same rule: the inner launch must be
foreground too, or the orphan failure simply moves one layer down. A launch
site is bound by the fork contract whether it is this skill's own or a
sub-agent's.

**Caller-side recovery.** If `/gaze <pr>` ever returns a bare fan-out
narration with no `## /verify-gate verdict` block (APPROVED/REROLL/ESCALATE),
treat it as a non-result: do **not** relaunch the reviewer battery. Wait for
the background reviewer notifications, then run `/verify-gate <pr>
worktree=$primary_root/.claude/worktrees/review-<pr-number>` directly to produce the verdict from their outputs.

**Fork liveness.** Once the phase 2–4 review comment has posted on the PR, the
caller must see either the phase-6 verdict comment or a bump log line within
`fork_liveness_seconds` (`skills/gaze/telemetry.yml`, env override
`GAZE_LIVENESS_WINDOW_S`; default 1200s / ~20 min) — same knob pattern as the
wall/token thresholds in § Telemetry. Two independent stalls landed in exactly
this window, both silent: 2026-07-11 (memory
`feedback_agent_stall_watchdog_recovery`) and 2026-07-13 (raid 291-245, PR
#551, where the review comment posted, then ~30 min of quiet: no simplify
commit, no verdict, review worktree mtime frozen).

**On window expiry, do not re-run phases 2–5.** Check three completion markers:
(1) a posted verdict comment, (2) branch-tip motion on the PR branch, (3) the
review worktree's file mtime. All stale/absent → invoke `/verify-gate`
directly, with the same invocation form as **Caller-side recovery** above
(one recipe, stated once), and continue the normal round
flow from its verdict; log a bump line on the ticket. The fallback skips only
the redundant phase 2–5 re-execution — verify-gate runs at full rigor and the
two-round cap is unaffected.

## Phases

### 1. Setup

Always invoke `/gaze` from within a conversation worktree, never from the main repo
root. The worktree is the isolation boundary; no main-repo checkout is ever needed.

**Isolation setup:**

```bash
# Step 1 — Resolve PR number to branch name (forge-specific step)
PR_BRANCH=<resolved-branch-name>

# Step 2 — Resolve the primary repo root, then create the worktree under its
# guarded `.claude/worktrees/` namespace (ticket 0300 — /tmp is outside every
# guard fast-path). `.claude/worktrees/review-*` is not whitelisted by name; it
# is covered by the same worktree-identity check as every worktree: an Edit/Write
# is allowed when the acting process is physically inside that worktree, denied
# otherwise — save the human-set `GUARD_ALLOW_PRIMARY_EDIT` escape hatch (the
# `projects/*/memory/*` exemption cannot match a review-* path). 0300 moved
# review worktrees here from /tmp for that coverage, not for a name allowlist;
# exact semantics live in `~/.claude/scripts/pretooluse-worktree-path-guard.sh`.
primary_root=$(git rev-parse --show-toplevel)
primary_root="${primary_root%%/.claude/worktrees/*}"   # strip if we run from a session worktree
git fetch origin "$PR_BRANCH"
git worktree add "$primary_root/.claude/worktrees/review-<pr-number>" origin/"$PR_BRANCH"
# The cwd-pinned reviewer agents and the REROLL fix agent run inside
# $primary_root/.claude/worktrees/review-<pr-number>; the main repo is never
# switched, never dirtied. (Exception: phase 5 /simplify is still a direct
# invocation and runs from the fork's own cwd, not review-<pr> — see its note below.)
```

On any exit path (APPROVED, REROLL-escalated, ESCALATE, circuit-breaker abort),
remove the worktree:

```bash
git worktree remove "$primary_root/.claude/worktrees/review-<pr-number>" --force
```

- Abort if not mergeable or if there are open merge conflicts.
- Collect:
  - The ticket file referenced in the PR title or body (`tickets/*.erg`).
  - PR body, full diff, all existing review comments, all inline comments, all commit
    messages on the branch.
- Check CI status for the merge request if the forge exposes it. If the forge CLI or API is unavailable, skip gracefully — CI status is informational only. If checks are configured and any are failing, note this in the setup summary; do not block on it (reviewer decides).
- Compute PR size: `git diff origin/main...HEAD --stat` → `pr_lines` (total insertions + deletions) and `pr_files` (files changed). Classify the battery **tier**:
  - **tiny** — `pr_lines ≤ 20` and `pr_files ≤ 2` and this is round 1.
  - **small** — `pr_lines ≤ 150` and `pr_files ≤ 5` and this is round 1 (and not already tiny).
  - **full** — everything else, and any round ≥ 2. The **tiny** and **small** tiers are round-1 classifications only; a round ≥ 2 is never tiny or small.

  The tier selects which reviewer agents run (see §§ 2–4, 5); phase 6 (`/verify-gate`) is **invariant** — it runs at every tier, never reduced. Per-tier battery:
  - **tiny** → Agent A (adherence) + phase 6 gate only. Skip Agent B (`/review`), Agent C (`/review-pr`), and phase 5 (`/simplify`) — each skip logged like the existing `review-pr: skipped (…)` line.
  - **small** → Agent A + Agent B + phase 5 (`/simplify`) + phase 6 gate. Agent C runs with the reduced "correctness only" perspective set (trivial risk, § 2–4) instead of the full five-perspective panel.
  - **full**, round 1 → the complete battery below, unchanged.
  - **full**, round ≥ 2 (i.e. the merge request already carries a prior Agent C review) → Agent A + Agent B + phase 5 (`/simplify`) + phase 6 gate; Agent C is scoped per § Round scoping below.
  Carry the resolved `tier` into the telemetry footer and the output-shape template (see § Telemetry, § Output shape).

- If any of these cannot be located, ESCALATE with a clear message. Do not proceed.

#### Round scoping

**Supersedes the #562 clause.** A round ≥ 2 still resolves to the **full**
tier, but its Agent C no longer re-runs the whole five-perspective panel by
default. Agent C re-runs the perspectives that objected in the previous round
plus one regression check over the cleared ones, per § Round scoping in
`skills/review-pr/SKILL.md` (ticket 0377). #562's lesson was that a round-2
battery was needed on an unchanged diff. That lesson is preserved by keeping
Agents A and B, phase 5, and the phase 6 gate at full strength every round.
What it does *not* justify is re-paying for perspectives that had nothing to
say.

**Reachable trigger.** The only entry into this branch is a *caller-level*
repeat `/gaze` on a merge request that already carries a prior Agent C
review: that invocation re-enters phase 1, reclassifies the tier, and finds a
review history. gaze's internal REROLL re-entry never reaches here — it
re-runs the **gate only** (§ Branch on verdict) and never returns to phase 1,
so round scoping neither widens nor narrows it. Two different counters share
the word "round", and they never interact: the REROLL round-1/round-2 cap
counts gaze's own internal fix-and-regate attempts *within* one invocation,
while the round scoped here counts the Agent C reviews posted on the merge
request *across* invocations.

**Relation to Convergence mode.** Convergence mode (ticket 0315,
§ Convergence mode, default off) decides at the caller layer whether a repeat
`/gaze` re-runs its panel at all; round scoping decides what that re-run panel
runs when convergence is **off** — with convergence on, the repeat is skipped
entirely and scoping never applies. Its flag is unaffected here.

**gaze does not compute the round.** It reads only whether a prior Agent C
review exists — a boolean from the merge request's review history, enough to
select the scoped branch — and passes no round number to Agent C. Agent C's
embedded procedure derives the round itself, exactly as § Round scoping in
`skills/review-pr/SKILL.md` prescribes: count the reviews this skill
previously posted on the merge request, identifiable by the verdict roster
those reviews always carry; the round is that count plus one.

An unchanged diff does **not** reset scoping. Reset happens only on a
substantial rewrite: the round's diff touches files the last review did not
cover, or changes more than roughly half of its lines. Then Agent C runs the
full panel for this round — scoping is ignored. The derived round number
itself is never mutated; only the scoping decision changes.

### 2–4. Read-only review fan-out (parallel)

These phases run as **Agent-spawned sub-agents, not `context: fork`
invocations** (ticket 0216). A fork does not inherit this skill's cwd or
conversation, so it lands in the session worktree on whatever branch is
checked out there — that is how a drifted fork pushed a stray branch and
opened rogue PR #243 (ticket 0193). Spawning an Agent fixes this
deterministically: each reviewer is a **read-only, foreground** Agent whose
cwd is **pinned to the existing review worktree** `$primary_root/.claude/worktrees/review-<pr-number>`
(created in phase 1). Foreground (`run_in_background: false`) is
load-bearing, not incidental — see **Fork execution contract** below: this
skill runs as a `context: fork`, and a fork cannot wait on background
agents. Do **not** give these agents `isolation: "worktree"` —
that cuts a *fresh* tree from the session repo on main/HEAD, which is exactly
the wrong-branch failure this conversion eliminates; only the REROLL fix
agent (a mutator) gets `isolation: "worktree"`.

Every reviewer agent's prompt:
- opens with `TASK DIRECTIVE — execute now`, naming the single sub-skill
  procedure it runs and the PR;
- forbids `cd` out of the pinned cwd, and forbids commits, pushes, new
  branches, new PRs, and any write to `tickets/*.erg` (read-only role);
- imperatively embeds the sub-skill's operating procedure (the steps below
  — not a `/skill` invocation), so the agent cannot misread the body as
  documentation;
- ends by **returning a single structured block as its final message**, which
  the orchestrator parses to branch.

Spawn the applicable agents **in a single message, as parallel foreground
Agent calls** (`run_in_background: false`) — the single message runs them
concurrently, and foreground makes the fork block until every one returns
before it proceeds. Do **not** launch them as background agents: a fork's
turn ends the moment it stops calling tools, and a background completion
re-invokes the MAIN loop, not the fork, so a background fan-out returns at
launch and orphans its reviewers (ticket 0250; see **Fork execution
contract**). Once all return, collect their structured outputs. Pin every
read-only reviewer to
**`model: sonnet`** — reviewers stay below the coder tier (rules/workflow.md
§ "Reviewer decorrelation"), and an unpinned Agent inherits the session
model, so on a top-tier session this fan-out is silently a top-model wave.

**Agent A — adherence** (`/verify-adherence <branch> worktree=$primary_root/.claude/worktrees/review-<pr-number>`
is the equivalent procedure). **Label-skip:** if the PR carries the
`verify:adherence-passed` label (set by `/hunt`'s pre-PR gate, see PR #40),
do **not** spawn this agent — the adherence check already ran clean before the
PR was opened. Otherwise spawn a read-only Agent, cwd `$primary_root/.claude/worktrees/review-<pr-number>`,
whose embedded procedure is: (1) cheap static checks — for each touched `.py`
under `scripts/`, probe import resolution (`uv run python -c "import sys;
sys.path.insert(0,'scripts'); import <m>; getattr(<m>,'<sym>')"`) and run each
touched module's test file (`uv run python -m pytest <files> -q`); both
blocking, <10 s budget, ESCALATE rather than trim. (2) Run the adherence suite
`uv run python -m pytest -m adherence -q` (with the legacy `test_hygiene_*` /
`test_discipline_*` / `test_schema_contracts` fallback for unmigrated repos);
failures are blocking. (3) If `pyproject.toml` names ruff and no test calls
ruff, emit one non-blocking `untested_rules` entry. (4) Only if a
`.claude/rules/*.md` file changed, run one semantic check citing file:line +
`suggested_test` per finding. Return the verdict block:
`adherence: PASS|FAIL`, plus `mechanical_failures`, `semantic_findings`
(each with `severity: blocking|nit`), and `untested_rules`. The orchestrator's
early-exit reads `adherence` and the count of `blocking` findings.

**Agent B — built-in review** (`/review`). **Tier-skip:** skip this agent when
the tier is **tiny** and log `review: skipped (tier: tiny)` in the setup
summary; it runs on the **small** and **full** tiers. This is a built-in slash command
whose procedure cannot be embedded as text, so it is **Agent-WRAPped, not
embedded**: spawn a read-only Agent, cwd pinned to `$primary_root/.claude/worktrees/review-<pr-number>`,
same containment rails, whose prompt simply invokes `/review` on the PR and
returns the review summary. (Phase 5 `/simplify` is the other built-in slash
command; it stays as a direct invocation for now — out of this ticket's scope —
and would be Agent-WRAPped the same way when converted. Until it is, `/simplify`
runs in the fork's own cwd — a sibling worktree, not review-<pr> — so the
worktree-identity guard denies its Edit/Write and it must apply fixes via Bash;
the Agent-WRAP is what lets those edits execute inside review-<pr>. Tracked at
ticket 0349.)

**Agent C — PR review** (`/review-pr <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`
or `/review-pr-prose <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`).
**Tier-gate:** skip this agent when the tier is **tiny** and log
`review-pr: skipped (tier: tiny, <pr_lines> lines, <pr_files> files)` in the
setup summary. When the tier is **small**, run it with the reduced **correctness
only** perspective set (the `trivial` risk band below) regardless of the risk
assessment. When the tier is **full** on round 1, run the full proportional
panel as assessed; when the merge request already carries a prior Agent C
review (the caller-level repeat `/gaze` case), run the panel scoped per
§ Round scoping — only the perspectives whose previous verdict was
comment/request-changes (prose: minor/major), plus one regression agent
running a single regression check over all the cleared ones, unless the diff
was substantially rewritten, in which case the full panel runs for this round
and scoping is ignored. Do **not** state a round number — gaze computes none.
Instead, have the embedded procedure instruct the spawned agent to derive the
round itself (count the reviews this skill previously posted on the merge
request, identifiable by the verdict roster they always carry; the round is
that count plus one), read the previous round's verdict roster, build the
scoped perspective list from it, and record the reason for each inclusion.
Spell that derivation out: the spawned agent does not read this file or
`skills/review-pr/SKILL.md`, so an unstated rule does not reach it.
Otherwise pick by file type: if any `*.qmd` changed → prose
panel; else code panel. Spawn a read-only Agent, cwd `$primary_root/.claude/worktrees/review-<pr-number>`,
whose embedded procedure is: read the linked ticket's exit criteria and the
diff, assess risk, and run the proportional perspective set in parallel —
**code:** correctness, consistency, scope, red-team, doc-propagation (trivial →
correctness only; standard → +consistency; +scripts → +doc-propagation;
substantial → all five); **prose:** discipline panel sized to the change,
always including an adversarial referee and an AI-tells auditor that scans the
full text against `config/ai-tells.yml`. Each perspective reports
confidence and a verdict (approve / comment / request-changes for code; accept
/ minor / major for prose). Synthesize: preserve dissent verbatim, dedupe, run
`make check`. Every non-blocker (minor) finding **must** carry exactly one tag
prefix — `verifiable:` (a reproducible failing assertion is attached),
`consider:` (hypothesis, no enforcement), or `nofollow:` (noted, not pursued);
hedged "might break X" phrasing is forbidden — produce the assertion or
downgrade to `consider:`. Blockers (request-changes / major) are untagged.
Post the single review on the PR and return the synthesized findings (blockers
+ tagged minors) as the structured block. This inner panel is itself a fan-out:
Agent C must launch its perspective agents **foreground**
(`run_in_background: false`), all in one message, and block until every one
returns before it synthesizes — the fork contract applies recursively (see
**Fork execution contract**; ticket 0263, `/gaze 479`, 2026-07-11).

Wait for all spawned agents to complete. Collect their structured outputs.

**Early-exit check**: if the adherence agent returned any `blocking` violations, skip phase 5 (simplify). Blocking adherence guarantees a REROLL; simplify tokens would be wasted. Log `simplify: skipped (adherence blocking)` in the telemetry phase line.

### 5. Simplify (sequential)

**Tier-skip:** when the tier is **tiny**, skip this phase and log
`simplify: skipped (tier: tiny)` in the telemetry phase line; it runs on the
**small** and **full** tiers. Otherwise, after 2–4 land their comments (and the early-exit check passes), run `/simplify <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`. This phase may commit fixes
to the PR branch. Wait for its fixes (if any) to land before the gate reads state.

### 6. Gate (the non-rubber-stamp step)

The gate also runs as an **Agent-spawned sub-agent, not a `context: fork`**
(ticket 0216) — same rationale as phases 2–4. Spawn one **read-only, foreground**
Agent (`run_in_background: false`, so the fork blocks on the verdict),
**`model: sonnet`** (a reviewer, below the coder tier), cwd **pinned to**
`$primary_root/.claude/worktrees/review-<pr-number>` (the equivalent fork call is
`/verify-gate <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`); never
`isolation: "worktree"`. Containment rails as above: no `cd` out of the pinned
cwd, no commits/pushes/branches/PRs; the gate's **one** permitted write is the
`${ERG:-erg} log <ticket-id> …` reroll-bump line (and its PR verdict comment) —
it edits no other `tickets/*.erg`. The agent's prompt embeds the gate procedure
imperatively and returns the YAML verdict block below as its **final message**;
the orchestrator parses `verdict` to branch.

Embedded gate procedure: for **every** ticket exit criterion, emit
ADDRESSED/MISSING with concrete evidence — a commit SHA + file:line that
touched the cited file, a matching test_id, or a posted rationale; "CI ran" /
"tests pass" is **not** evidence. For **every** review comment (from the phase
2–4 agents or a human), mark ADDRESSED (a post-comment commit changed the cited
file, OR the comment is resolved, OR a follow-up ticket is referenced) or
UNRESOLVED. Tagged minors are triaged by tag, not severity: `verifiable:`
unresolved → blocker-adjacent (REROLL); `consider:` informational; `nofollow:`
muted; untagged minors → `malformed_minors` (round 2 → ESCALATE). Every
must-fix simplify finding is APPLIED (diff shows it) or has a validated
rationale. Any `blocking` adherence violation → REROLL. Run `git log
origin/main..origin/<branch> --stat` (two-dot) and report files not traceable
to an exit criterion as `scope_overflow` (report only — never rebase/amend to
excise). Decision: any MISSING criterion, any unresolved human comment, any
unresolved `verifiable:` minor, any unapplied must-fix, any blocking adherence,
or any `scope_overflow` with disposition ESCALATE → REROLL (round 1) / ESCALATE
(round 2); all lists empty and all criteria ADDRESSED → APPROVED. Round 3 is
forbidden. On REROLL run `${ERG:-erg} log <ticket-id> "bump verify-reroll —
round {n}: {top unresolved criterion}"` and post the PR verdict comment. Return:

```yaml
verdict: APPROVED | REROLL | ESCALATE
per_exit_criterion: [...]
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
unresolved_adherence_violations: [...]
rationale: <paragraph>
round: 1 | 2
```

## Branch on verdict

- **APPROVED** → post a "verify: approved" comment on the PR summarising the evidence. End
  the skill. The caller merges.
- **REROLL, round 1** → spawn a fix subagent with `isolation: "worktree"`,
  `model: opus` (a mutator/coder — top available tier where it earns its keep, not the
  reviewer's sonnet; effort is not an Agent launch param, so it tracks the
  session effort), launched **foreground** (`run_in_background: false`, so the
  fork blocks until it pushes — see **Fork execution contract**), feeding it the unresolved lists as input. Fix agent gets ≤10 min. On push, **re-enter phase 6 by
  re-spawning the read-only gate Agent** (pinned cwd `$primary_root/.claude/worktrees/review-<pr-number>`, as in
  phase 6) with `round=2` — not a fork invocation.
- **REROLL, round 2** → upgrade to ESCALATE (no third round). Post a PR comment with the
  still-unresolved items and the gate's rationale. End the skill.
- **ESCALATE** → post a PR comment tagged `/gaze stopped:` listing what needs human
  judgment. End the skill.

## Containment postcondition

On **every** exit path (APPROVED, REROLL-escalated, ESCALATE, circuit-breaker
abort), after removing the review worktree and before returning control to
the caller — the caller must see this report before any merge step:

```bash
git rev-parse --show-toplevel               # FIRST: confirm cwd is the session
                                            # worktree — the forks just returned,
                                            # so a drifted cwd would make the two
                                            # reads below report a foreign tree's
                                            # state (rules/git.md § anchor)
git status --porcelain                      # invoking session worktree
git branch --show-current                   # must equal the branch on entry
git -C <primary-repo-root> status --porcelain
```

- **Foreign files** (anything this run did not deliberately create —
  especially stray `tickets/*.erg`) → remove or restore them, and flag the
  contamination in the verdict comment. Do not leave them for a later
  `git add` to sweep.
- **Unexpected branch** → switch back to the entry branch and flag it. Never
  end the skill with the session worktree on a different branch than it was
  on at phase 1. This runs right after the review forks return, so the shell
  cwd may sit in a foreign worktree: confirm the tree first
  (`git rev-parse --show-toplevel` should equal the session worktree), then
  anchor the corrective switch — `git -C <session-worktree> switch <entry-branch>`,
  not a bare `git switch` against an assumed cwd (rules/git.md § anchor across
  a forked-skill boundary).
- Anything that cannot be restored cleanly → downgrade the verdict to
  ESCALATE; a contaminated workspace must not feed a merge.

## Fix-agent contract

The subagent spawned on REROLL receives:

- Worktree path (PR branch already checked out).
- Unresolved lists from the gate verdict (review comments, simplify findings, adherence
  violations, per-exit-criterion gaps).
- Strict rule: **only** the listed items. No scope creep. No "while I'm here" edits.
- TDD discipline still applies: add a failing test for any behavioural fix before coding.
- Test-run budget: `make check-fast` plus the tests implicated by the unresolved-items list during the fix; one full `make check` before the final push — not per fix.

Push commits to the PR branch; do not open new PRs. Trigger re-entry into phase 6.

## Circuit breakers

- Setup step cannot find ticket file → ESCALATE.
- Any of phases 2–5 errors or times out → ESCALATE (do not silently skip). Exception: phase 5 (simplify) intentionally skipped when adherence is blocking — this is not an error.
- Fix agent timeout (10 min) → ESCALATE.
- Gate disagrees with phase 2–5 on a must-fix finding → ESCALATE (no silent resolution).
- Two REROLL rounds reached → ESCALATE.
- Telemetry thresholds (see `## Telemetry`).

On **every** circuit-breaker exit (not only ESCALATE): run
`git worktree remove "$primary_root/.claude/worktrees/review-<pr-number>" --force` before returning so the
main repo is never left in a partial state.

## Telemetry

### Per-phase timing (stderr only)

Each phase emits start/end lines: `[verify] phase=<name> start=<ISO> / end=<ISO> elapsed=<s>s`

### Verdict footer (PR comment)

Appended to verdict comment: `telemetry: tier=<tiny|small|full> wall=<s>s agents=<n> tokens=<in+out> cost~=$<usd>`

Fields: `tier` (battery tier from phase 1 — `tiny|small|full`), `wall` (phase-1 to
verdict), `agents` (sub-agent count), `tokens` (sum, use `na` for missing),
`cost~=` (best-effort USD, `na` if incomplete).

### Thresholds

Read from `skills/gaze/telemetry.yml`; env vars override. Defaults:
wall warn=15min escalate=30min; tokens warn=500k escalate=1M; fork liveness
window=20min (monitored by the caller, not checked at internal phase
boundaries).

On warn: post `/gaze: slow run` comment, continue. On escalate: stop, post
`/gaze stopped:` with measured value. Escalate > warn. Check at phase boundaries
only — except fork liveness, which a silent fork cannot self-check, so the
caller monitors it (§ Fork execution contract).

## Convergence mode (ticket 0315, measure-B pre-registration)

An **opt-in** experimental flag for the phase-5 measure-B A/B (see
`docs/trace-ab-2026-06.md`). It governs **caller-level** re-invocation of
`/gaze` on a PR that already carries a completed full gaze round — not the
internal round-1 REROLL re-entry branch (§ Branch on verdict), which is already
gate-only and stays unchanged.

When `convergence.enabled` is true (`skills/gaze/telemetry.yml`, env override
`GAZE_CONVERGENCE_ENABLED`) **and** the PR already carries a completed full
gaze round (a prior `/verify-gate verdict` comment from an earlier invocation),
a repeat `/gaze` invocation runs **phase 6 (verify-gate) only** — no phases 2–5
panel re-run. Default **off** = current practice, so live behaviour is
unchanged until the B-arm week flips it on.

## `--force-approve`

Explicit human override. Usage: `/gaze <pr-number> --force-approve <reason>`.

- Skips phase 6 gate.
- Posts a loud PR comment: `/gaze: force-approved — reason: <reason>`. Includes the
  outputs of phases 2–5 so reviewers see what was waived.
- Logs the override in the skill transcript.
- Still does not merge.

## Not in scope

- **Wave-level integration review.** Verify one PR at a time. Use a separate
  `/verify-wave` (not yet drafted) for post-merge integration testing of a batch.
- **Merging.** Ever. That is the caller's job.

## External reviewer panel

The external, decorrelated reviewer panel — sandboxed CI-style seats over
agnostic CLI reviewers — is managed by the `/reviewers` skill, not inlined
here; seat execution is the 0217 seat-runner. See `skills/reviewers/SKILL.md`.
This section is the panel-extension contract (ticket 0205).

**When seats fire.** Automatically, on **small**- and **full**-tier CODE
reviews — the decorrelation evidence concentrates ensemble value on
substantive multi-file code changes. Skip on the **tiny** tier and on prose
panels (any `*.qmd` changed). Empty roster or `/reviewers` unavailable →
skip silently: the panel is fail-open and never blocks a gaze run.

**How.** At the phase 2–4 reviewer-battery launch, also invoke
`/reviewers request <pr>` as a background *shell* job (a Bash call, not an
agent launch, so the fork-orphan contract does not apply): the sandboxed
seats (~30–120 s) run concurrently with the internal reviewer battery and
finish well inside its wall time. Before phase 6, run
`/reviewers harvest <pr>` synchronously and hand the normalized
`verifiable:` / `consider:` findings to the gate as panel comments.

**Disposition.** The gate dispositions external findings identically to
internal ones (0205 rule 1). Seats are **advisory**: only verifiable-class
findings may bounce. A seat that errors or hangs WARNs and the review
proceeds — per-seat fail-open; one seat never blocks the verdict.

**Scorecard (the trial).** After the gate verdict, for each seat that
returned findings, append the trial line:
`/reviewers scorecard <pr> <seat> "<verdict — N verifiable, M consider, of
which K adopted>"`. This fills ticket 0207's advisory trial (≥5 MRs across
≥3 projects per config) passively from normal gaze runs.

**Advisory → required promotion** (0205 rule 2, condensed). A seat runs
advisory for at least 5 merge requests spanning at least 3 projects before
promotion. Promotion is flipping its check from optional to required — a
manual roster edit by the author, never automatic. LLM review is
non-deterministic: promote only seats whose verifiable-class findings are
stable across re-runs; advisory is the safe default.

**Forge automated reviewer** (ticket 0206): the gate's comment-validation
step includes the forge's automated reviewer (e.g. a requested Copilot
review), when present. Its findings are dispositioned like any panel
comment: correctness-class only may bounce, style is noted-not-blocking.
The seat is **on-demand**: a PR nobody requested it on is simply a PR
without that seat, with no warning and no wait. Only when a request WAS
made (the bot appears in the PR's requested or completed reviewers) and
its review is still pending while everything else is ready: bounded wait
of a few minutes, then proceed with a logged WARN — fail-open.
<!-- harness-extension-point: requested-reviewer detection is
`gh pr view <pr> --json reviewRequests,reviews` on GitHub. -->

## Output shape

Post a single top-level PR comment at end of skill. Two sections,
always both present. No interim "started"/"finished" chatter — the
final report is the signal.

```
## /gaze actions

round: <n>
tier: tiny|small|full
adherence: PASS|FAIL — <n_blocking> blocking
review: <n_comments_posted> | skipped (tier: tiny)
review-pr: <n_comments_posted> | skipped (tier: tiny) | skipped (adherence blocking)
review-pr scope: full panel | scoped: <objecting perspectives> + regression (omit if round 1)
simplify: <n_fixes_applied> | skipped (tier: tiny) | skipped (adherence blocking)
fix agent: <n_commits> commits (round 2 only, omit if round 1)

## /verify-gate verdict

verdict: APPROVED|REROLL|ESCALATE

Exit criteria:
- <criterion 1>: ADDRESSED — <evidence>
- <criterion 2>: MISSING — <gap>

Unresolved review comments: [list or "none"]
Unresolved simplify: [list or "none"]
Adherence: PASS | FAIL (<count>)

Rationale:
<paragraph>

telemetry: tier=<tiny|small|full> wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
```

On `--force-approve`, Part A is annotated `FORCE-APPROVED by <reason>`
and Part B shows the gate's would-have-been verdict before override.
