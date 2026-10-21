---
metadata:
  category: build
name: gaze
description: "Review one merge request: adherence check, code or prose review panel, simplify. Returns REVIEWED / FINDINGS / ESCALATE and never APPROVED; the merge gate is /verify-gate, run by the caller. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> [--waive-breaker <reason>] [--force-approve <reason>]"
context: fork
# Background by intent: /gaze is long-running, and a raid wave gates several PRs
# at once — backgrounding the orchestrator is what lets those run concurrently.
# This matches the Claude Code 2.1.218 default; pinned explicitly so a future
# default flip cannot serialize a wave silently. Its own sub-skills and reviewer
# agents are waited for by polling (see "Fork execution contract" below) — the
# two are different axes: parallelism comes from concurrent tool calls inside one
# message, never from backgrounding a phase this skill must wait on.
background: true
---

# Gaze — review PR $ARGUMENTS (gaze reviews, verify-gate gates)

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

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

One skill, one PR, one review result: REVIEWED / FINDINGS / ESCALATE. **Gaze
reviews; `/verify-gate` gates.** Gaze never returns APPROVED, REROLL or
NEEDS-AUTHOR: those are gate verdicts, ruled by the caller's `/verify-gate`
run on the reviewed head. **Does not merge** — the merge decision belongs to
the caller (the human or the raid).
Only one live `/gaze` may run on a PR at a time; the caller keeps to that
(`rules/workflow.md` § Delegation). A past verdict is evidence, not authority
to overwrite or call it fabricated: inspect its gate identity and ruled tip.

## When to use

- Raid Phase 6 (per-ticket review before the gate).
- Any time an author wants a full-depth check on a single PR before asking for merge.
- **Do NOT** use for quick sanity — use `/review` or `/review-pr` directly.

## Invariants

- Runs on exactly one PR.
- Never returns APPROVED: a test pins it (`tests/test_gaze_never_approves.py`).
  `REVIEWED` means no blocking finding on the reviewed head, nothing more.
- Does not run `/verify-gate`. The caller runs it after gaze, and again after any fix.
  The review worktree is removed before gaze returns; the gate creates its own.
- Does not merge. The result is structured output; the merge decision belongs to the caller.
- The only commits gaze makes on the PR branch are the bounded phase 5 simplify fixes; no changes to other branches.
- `--force-approve` is supported for explicit human override; it skips the review and
  is logged loudly in the PR comments and the skill transcript. It is an override
  record, not a verdict.
- `--waive-breaker <reason>` lifts only the un-reviewable file-count stop. The battery
  and simplify still run; gaze records the waiver and the caller passes it to
  `/verify-gate`, which rules NEEDS-AUTHOR (§ Waiver).
- **Cross-repo prerequisite**: the caller must ensure cwd is the target project before
  invoking `/gaze`. The skill and its sub-skills (`/review-pr`, `/simplify`, etc.)
  use `gh` and `git` commands that resolve against cwd.
- **Branch-currency prerequisite**: the caller rebases the PR branch onto current
  `origin/main` and force-pushes with lease before invoking (`rules/git.md`
  § Merging) — a gate validates the *combination* branch ⊕ base, so a verdict
  computed on a stale base is partially void. `/gaze` does not rebase the
  branch itself; that is a caller-side step, not a phase here.
- **Quiet-branch prerequisite**: never start `/gaze` while that branch's coding
  lead is still live. Gaze reviews a head the lead may move under it, and
  its phase 5 simplify fixes would then commit on top of work in flight.


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
request. That comment is evidence, not a gaze result: without an accepted gaze
result there is no gate. Re-run `/gaze <pr>` once if the liveness window below
allows it; otherwise park the PR and ESCALATE to the author, as `raid` and
`merge` do for a missing result. Once a result is accepted, the gate reads a
waiver only from an already-posted waived `circuit_breaker` header in the PR's
comments; if none was posted, a waived 15+ file PR is ESCALATE there
(fail-safe), as is an un-waived one.

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
review worktree's file mtime. All stale/absent → no accepted gaze result, so no gate: park the PR and
ESCALATE to the author (the window is spent, so no re-run). The check skips only
the redundant phase 2–5 re-execution; it never substitutes a direct
`/verify-gate` for the missing result.

## Phases

### 1. Setup

Always invoke `/gaze` from within a conversation worktree, never from the main repo
root. The worktree is the isolation boundary; no main-repo checkout is ever needed.

**Isolation setup:**

```bash
# Step 1 — Resolve PR number to branch name (forge-specific step)
PR_BRANCH=<resolved-branch-name>

# Step 2 — Resolve the primary repo root, then create the worktree under its
# `.claude/worktrees/` namespace (ticket 0300), where the runtime's worktree
# isolation covers it like every other worktree; never under /tmp.
primary_root=$(git rev-parse --show-toplevel)
primary_root="${primary_root%%/.claude/worktrees/*}"   # strip if we run from a session worktree
review_tree="$primary_root/.claude/worktrees/review-<pr-number>"
git fetch origin "$PR_BRANCH" || exit 1
if ! git worktree add "$review_tree" origin/"$PR_BRANCH" || ! test -d "$review_tree"; then
    echo "gaze: cannot create isolated review worktree for PR <pr-number>; refusing to fall back into the invoking tree" >&2
    exit 1
fi
# The reviewer agents (review worktree via git -C) run inside
# $primary_root/.claude/worktrees/review-<pr-number>; the main repo is never
# switched, never dirtied. (Exception: phase 5 /simplify is still a direct
# invocation and runs from the fork's own cwd, not review-<pr> — see its note.)
```

- Abort if not mergeable or if there are open merge conflicts.
- Collect:
  - The ticket file(s) referenced by PR-body close claims (`tickets/*.erg`);
    include any title/body reference when no close claim exists. No close
    claim and no title/body reference → proceed with `ticket: none`; the gate
    reviews against the PR body (`/verify-gate` § Circuit breakers).
  - PR body, full diff, all existing review comments, all inline comments, all commit
    messages on the branch.
- Check CI status for the merge request if the forge exposes it. If the forge CLI or API is unavailable, skip gracefully — CI status is informational only. If checks are configured and any are failing, note this in the setup summary; do not block on it (reviewer decides).
- First run `python3 "$IDH_ROOT/scripts/review-pr-anchor.py" <pr-number> --worktree "$primary_root/.claude/worktrees/review-<pr-number>"`. A nonzero `REVIEW-ANCHOR:` result stops the battery: do not review an empty or wrong-tree diff. Carry its HEAD and changed-file roster into every review prompt.
- Compute PR size rename-aware: `pr_lines` = total insertions + deletions from `git diff origin/main...HEAD --stat`; `pr_files` = the CONTENT-BEARING entry count from `git diff --name-status -M origin/main...HEAD` — added, modified, and deleted each count 1; cross-reference rename entries with `git diff --numstat -M origin/main...HEAD`: a rename counts 1 iff its additions + deletions > 0, otherwise 0 (a genuinely content-free pure rename has zero line change in rename-aware numstat; R100 alone is insufficient because the similarity index ignores line order) — pure renames add no review load, and counting them via `--no-renames` inflates consolidation diffs past the breaker on arithmetic (ticket 1026, observed on PRs #1178/#1179).

  Size has one use: the un-reviewable breaker below. It selects no battery
  tier; every PR gets adherence, the review panel and simplify. Panel width is
  review-pr's own decision (`skills/review-pr/panel-width.json`, `review:standard`).
  Compute the path-risk band once, for the comment, with
  `cd $primary_root/.claude/worktrees/review-<pr-number> && python3 "$IDH_ROOT/scripts/prose_predicate.py" --risk <changed files>`
  (`high|low|normal`); it is carried to `/verify-gate`, never used to skip a phase here.

- **Preflight before spawning phases 2–5.** Count distinct ticket close-claims
  from the PR **body**, using the same line grammar as `erg-pr-merge`: bold or
  bare `Ticket: tickets/NNNN...` lines count; the title, `Ticket-ref:` lines,
  `Ticket: none`, and repeated claims for one ID do not. For example, extract
  IDs with `grep -oiP '^\*{0,2}ticket:?\*{0,2}:?\s*tickets/\K\d+' | sort -u`.
  If the count is two or more, record `multi_ticket: <IDs>` as a **non-blocking**
  finding for `/verify-gate` to disposition. Below the size breaker, continue the normal review;
  genuinely bundled tickets are permitted by `rules/git.md` § Merging.
- If `pr_files >= 15` and no waiver is recorded (see **Waiver** below), the PR exceeds the **15+ content-bearing files** monster threshold
  borrowed from `rules/workflow.md` § Ticket discipline for multi-PR work. Return ESCALATE
  immediately, before spawning any phase 2–5 reviewer,
  with `circuit_breaker: un-reviewable` and reason
  `un-reviewable: <pr_files> content-bearing files / <pr_lines> lines — split before review`.
  When `multi_ticket` is present, add that the combined tickets are a
  decomposition signal. Post the result comment with the
  breaker and `battery: skipped (un-reviewable)` visible; the caller's
  `/verify-gate` re-counts the files itself and ESCALATEs the same way.
  Cleanup and containment
  still run. An explicit `--force-approve <reason>` overrides this breaker
  loudly under the existing override contract; record the waived breaker and
  size in its PR comment. `--force-approve` runs no review at all (§ `--force-approve`);
  a waiver below is the way to keep review on an oversized PR.
- A recorded waiver (`--waive-breaker` or the PR-body `Review-scope: indivisible` line) lifts only this stop; its rules are in § Waiver below.

- ESCALATE with a clear message, and do not proceed, only if a close claim names a nonexistent ticket file or the PR body, diff or comments cannot be located. A missing ticket with no claim and no reference is not an escalation.

#### Round scoping

A repeat `/gaze` on a merge request that already carries a prior review-pr
review does not re-run the whole five-perspective panel by default: review-pr
re-runs the perspectives that objected plus one regression check over the
cleared ones (§ Round scoping in `skills/review-pr/SKILL.md`, ticket 0377).
Adherence and simplify run at full strength every time.

**gaze does not compute the round.** It reads only whether a prior review-pr
review exists (a boolean from the merge request's review history) and passes no
round number. review-pr derives the round itself: count the reviews it
previously posted on the merge request, identifiable by the verdict roster they
always carry; the round is that count plus one.

An unchanged diff does **not** reset scoping. Reset happens only on a
substantial rewrite: the diff touches files the last review did not cover, or
changes more than roughly half of its lines. Then the full panel runs for this
round and scoping is ignored.

#### Waiver

The 15-file count is a decomposition signal, not a hard wall. A waiver lifts
only the file-count stop. It never lifts the review, simplify or any other
breaker, and gaze never approves a waived PR: the caller passes the waiver
record to `/verify-gate`, which rules NEEDS-AUTHOR on a passing waived PR, and
only the author decides to merge it.

**Declaring.** `--waive-breaker <reason>` on the `/gaze` invocation, or a
PR-body line `Review-scope: indivisible — <reason>`. The author writes either.
Gaze does not check who wrote it; the gate judges the diff (`verify-gate`
§ Indivisibility). The change must be indivisible: a pure rename or rewire with
no independent change that could land alone.

**Recording.** Read in phase 1, before any reviewer spawns. Record the waiver
with `pr_files`, `pr_lines`, the reason and its source (flag or body line) in the
PR comment, and set the header to
`circuit_breaker: waived (<pr_files> content-bearing files / <pr_lines> lines — <reason>)`.
The round-1 header is the baseline for growth.

**Scope.** Growth is measured against the earliest posted waived header, not the
phase-1 recount of a later round, because a recount absorbs the very growth it
should catch. Growth past that baseline makes the PR un-reviewable:
`circuit_breaker: un-reviewable`, ESCALATE. A waiver beside two or more close
claims is flagged as `multi_ticket`, as in the preflight above. Every later
comment of a waived PR repeats the header
`circuit_breaker: waived (<pr_files> content-bearing files / <pr_lines> lines — <reason>)`
so the gate reads one format.

### 2–5. Review and simplify

The review panel is `/review-pr` (code) or `/review-pr-prose` (manuscript), invoked directly with the review worktree; there is no gaze-specific reviewer agent and no size tier.

### 2–4. Read-only review fan-out (parallel)

Agent A (adherence) and the optional adapter seats run as **Agent-spawned
sub-agents, not `context: fork` invocations** (ticket 0216); Agent C is a direct
invocation of the review skill (below). A fork does not inherit this skill's cwd or
conversation, so it lands in the session worktree on whatever branch is
checked out there — that is how a drifted fork pushed a stray branch and
opened rogue PR #243 (ticket 0193). Spawning an Agent fixes this
deterministically: each reviewer is a **read-only** Agent that
operates on the existing review worktree
`$primary_root/.claude/worktrees/review-<pr-number>`
(created in phase 1) via `git -C` — never assume the spawned agent's
own cwd is the review tree; how a runtime sets a spawned agent's cwd
is not portable, `git -C` is (ticket 0853). Waiting on a written artifact, not on a return value, is
load-bearing, not incidental — see **Fork execution contract** above: this
skill runs as a `context: fork`, and a fork cannot wait on background
agents.

If the battery cannot be launched at all — the runtime refuses the
spawn, the agent connector is absent, or the spawn-depth limit is hit — first
attempt the detached-seat substitution documented in
`skills/review-pr/SKILL.md`; if that also cannot run, emit a one-line
`battery: NOT-RUN — cause: <guard|no-agent-tool|depth>` in the result
comment. The boundary with the seat-level signal: no seat launched at all is
a battery NOT-RUN; seats launched but reports missing stays seat-level
`PANEL-INTEGRITY:` (whose name is unchanged). The NOT-RUN line names a launch
failure, not a review finding: never fabricate findings. The result is capped
at ESCALATE, never APPROVED (gaze returns no approval at all).

Every reviewer agent's prompt:
- opens with `TASK DIRECTIVE — execute now`, naming the single sub-skill
  procedure it runs and the PR;
- forbids commits, pushes, new branches, new PRs, and any write to
  `tickets/*.erg` (read-only role);
- runs every git read as
  `git -C "$primary_root/.claude/worktrees/review-<pr-number>" ...` —
  it never assumes its own cwd is the review tree (portable across
  runtimes);
- bans working-tree overwrites outright: no `git checkout <ref> -- `,
  no `git restore .`, no `git reset --hard`; inspect another version
  with `git show <ref>:<path>` (rules/git.md);
- refuses and reports NOT-RUN if the review worktree is unreachable, or
  its HEAD differs from the anchor HEAD carried in the prompt — it never
  falls back to the session cwd;
- carries its procedure: Agent A invokes the live adherence contract as
  specified below; the portable simplify reviewer gets the phase 5 steps;
- ends by **returning a single structured block as its final message**, which
  the orchestrator parses to branch.

Spawn the applicable agents (Agent A and any adapter seats; not Agent C, which
is invoked directly) **in a single message, as parallel background
Agent calls**, each writing its result to the phase artifact path — the single message runs them
concurrently, and the bounded poll on those artifacts is what makes this fork wait
before it proceeds. Keep polling until every artifact lands: a fork's
turn ends the moment it stops calling tools, and a background completion
re-invokes the MAIN loop, not the fork, so a fork that stops polling returns at
launch and orphans its reviewers (ticket 0250; see **Fork execution
contract**). Once all return, collect their structured outputs. Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); seats that must be independent follow
`skills/route/references/decorrelation.md` ("The launch line"): scale to the risk; a high-risk PR needs one
cross-family detached seat, else `no report` and `PANEL-INTEGRITY: DEGRADED`.

Seat defaults are guidance, not pins; raise a seat when the change warrants it:

| Seat | Default worker class | When to raise |
|---|---|---|
| adherence, scope, docs-propagation, consistency | cheap cluster | a rule is subtle or the diff is large |
| correctness | mid-size model | high-risk or cross-cutting change |
| red team | mid-size model | high-risk change: another family (`decorrelation.md`) |

**Agent A — adherence** (`/verify-adherence <branch> worktree=<absolute-review-worktree>`).
**Label-skip:** if the PR carries the
`verify:adherence-passed` label (set by `/hunt`'s pre-PR gate, see PR #40),
do **not** spawn this agent — the adherence check already ran clean before the
PR was opened. Otherwise the launch is **the adherence-seat profile**
(`agents/adherence-seat.md`), whose contract is
`profiles/adherence-seat/PROFILE.md`: spawn it on the review worktree
`$primary_root/.claude/worktrees/review-<pr-number>`, the branch and the
worktree path riding in the launch prompt — the seat's rails (read-only,
`git -C` discipline, artifact protocol) are the contract's and are not
restated in this launch block. Its FIRST action is to invoke the live contract:

<!-- harness-extension-point: runtime skill-loader invocation. -->
```
Skill(skill: "verify-adherence", args: "<branch> worktree=$primary_root/.claude/worktrees/review-<pr-number>")
```

Substitute the resolved branch and absolute review-worktree path in the args.
Pass through `trace=<path>` when the caller supplied it. Do not embed or
reimplement the verification steps here: the skill loader supplies the current
procedure, including project-runner discovery, reference resolution, and trace
checks. Wait for completion and return its structured verdict unchanged:
`adherence: PASS|FAIL`, plus `mechanical_failures`, `semantic_findings`
(each with `severity: blocking|nit`), and `untested_rules`. The orchestrator's
early-exit reads `adherence` and the count of `blocking` findings. Propagate
ESCALATE, a timeout, or an unparseable result as an infrastructure failure;
never replace a missing verdict with PASS. Write the result to Agent A's
phase artifact using the same completion protocol as the other reviewers.

**Native `/review` and `/simplify`** are optional adapter seats, never the
basis of the review. Phase 5 uses native `/simplify` when available and the
portable procedure below otherwise, both directly invoked (ticket 0349) and both
targeting the explicit review worktree and PR branch.

**Hand native `/review` the resolved axes; it guesses without them.**
`/review` checks prose against a house rulebook and, told nothing, picks one by
inference: on a manuscript merge request it read `rules/doctype/book.md` where
the project manifest declares `techreport` (audit of 2026-08-17, MR 136).
Before spawning that seat, run
`cd $primary_root/.claude/worktrees/review-<pr-number> && python3 "$IDH_ROOT/scripts/prose_predicate.py" --axes <changed files>`
and carry its lines verbatim into the wrap prompt. Same cwd anchoring and same
refusal semantics as the routing call below, since this reads the disk too.
Routing picks which panel reviews the diff; the axes tell the reviewer which
rulebook to hold it to.

**Agent C — PR review** (`/review-pr <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`
or `/review-pr-prose <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`).
This is the one launch mode: gaze invokes the review skill directly with the
review worktree, never through a spawned wrapper agent carrying an embedded
copy of the panel. There is no gaze-specific reviewer agent; the invoking
fork's own toolset supplies the delegation capability.

**Route first.** Choose the skill by the shared prose predicate, anchored in the
review worktree — the predicate reads the disk (manifest walk-up,
`\documentclass` sniff), so a parked cwd would return a plausible, wrong
verdict. Run
`cd $primary_root/.claude/worktrees/review-<pr-number> && python3 "$IDH_ROOT/scripts/prose_predicate.py" <changed files>`
— it prints `prose` when any changed file resolves to a `doctype` (from the
project's `.claude/rules-map.toml` manifest, else the `\documentclass`
sniff; one manuscript flips a mixed diff), `code` otherwise. It refuses any
path that does not exist under that cwd (exit 2, no verdict) — treat a
refusal as a routing error to fix, never as `code`. Process prose — notes,
tickets — carries no doctype and stays on the code panel, which is the panel
the audit measured as correct for it (ticket 0550). `prose` →
`/review-pr-prose`; `code` → `/review-pr`.

**What the review skill owns; gaze passes it nothing but the PR and tree.**
Panel width is review-pr's: `skills/review-pr/panel-width.json` (`max_lines`,
`max_files`, `pipeline_paths`) picks Correctness only for a qualifying round-1
code diff and at least Correctness + Consistency otherwise; `review:standard`
or a Correctness concern widens it to all five. It also owns the round number
and § Round scoping for a repeat review, the detached-seat substitution, the
project gate run, minor tags (`verifiable:` / `consider:` / `nofollow:`) and
the single posted review. Gaze passes no round number and no perspective list.

Inside the review skill the selected perspective agents launch in parallel,
each writing its own artifact, and the skill polls them against its manifest under a bounded
deadline before it synthesizes; gaze's fork waits on the skill's return, so
the fork contract holds one layer down.

**Panel integrity in gaze's result.** If the review skill itself cannot launch,
or reports that the Agent tool is unavailable or a spawn failed, gaze does not
substitute its own sequential review: it records the failure, marks the review
unresolved and claims no completed review round. Carry the exact
`PANEL-INTEGRITY:` line the skill posted (`PANEL-INTEGRITY: DEGRADED — Agent
tool unavailable or spawn failed; selected perspectives not run`, or `missing
perspective report: <name>` for a perspective still missing at the bounded collection deadline) and its `dissent: unavailable` into the /gaze result comment, and use
`panel integrity: DEGRADED` there. Never write `dissent: none` for this path.
When the invoking toolset lacks the Agent tool, the review skill first applies
the detached-seat substitution in skills/review-pr/SKILL.md instead of degrading.

Wait for all spawned agents to complete. Collect their structured outputs.

**Early-exit check**: if the adherence agent returned any `blocking` violations, skip phase 5 (simplify). Blocking adherence guarantees FINDINGS; simplify tokens would be wasted. Log `simplify: skipped (adherence blocking)` in the telemetry phase line.

### 5. Simplify (sequential)

**Prose-skip:** when the diff routed prose (the same
`"$IDH_ROOT/scripts/prose_predicate.py"` verdict the phase 2–4 panel choice used), skip
this phase and log `simplify: skipped (prose workpackage)` in the telemetry
phase line. Motive: this phase may commit to the PR branch, and `rules/git.md`
§ Prose workpackages forbids autonomous edits to a manuscript — an autonomous
change to prose goes through its own branch + merge request for the author to
arbitrate, never through a review-phase auto-fix (ticket 0550: two runs on the
same file decided this in opposite directions the same day; the rule now
exists). Otherwise, after 2–4 land their comments (and the early-exit check passes),
perform one of these routes. Record `simplify route: native|portable`.

- **Native command available:** run `/simplify <pr-number> worktree=$primary_root/.claude/worktrees/review-<pr-number>`.
- **Native command absent:** launch a separate reviewer through the active
  runtime (model chosen per launch from the `route` skill), using the phase artifact
  and bounded-wait contract above. Give it the explicit PR number, review tree,
  base ref, anchor HEAD and changed-file roster. It runs the review-anchor check
  before and after examining `git -C <review-tree> diff origin/<base>...HEAD`
  and the relevant surrounding code or instructions. It must look for
  unnecessary complexity, duplication, opportunities to reuse existing
  mechanisms, and safe simplifications that preserve behavior and ticket
  intent. This is a distinct simplification pass, not reuse of a general
  review's approval. It returns the reviewed SHA, paths examined, and actionable
  findings with severity, location, proposed change and rationale; or a CLEAN
  verdict explaining the concrete candidates considered and why they need no
  change. An absent reviewer, timeout, anchor mismatch, wrong diff or missing
  evidence means this phase is unresolved and triggers the existing breaker;
  absence of the slash command alone does not.

For either route, the orchestrator applies bounded fixes only to the PR branch
in the explicit review tree, or records an evidence-backed disposition for each
finding. Run affected checks for changes, commit and push fixes, and wait for
completion before the result is read. After any fixes, anchor the final HEAD
again and have the simplification reviewer confirm the dispositions against
that head; update the artifact with the final reviewed SHA. A moved head without
this confirmation leaves the pass unresolved. Feed all findings and dispositions
(or the evidenced CLEAN result), route, and reviewed SHA in the result. The
same must-fix rules apply to both routes; no portable route silently skips or
weakens the phase. The prose and adherence skips above remain unchanged.

### External reviewer panel (optional, beside phases 2–4)

External, decorrelated review is optional evidence routed by the active
runtime. When useful or requested, describe the expertise, capability and
independence needs through `skills/reviewers/SKILL.md` and read its live-route
reference. The runtime discovers available reviewers and chooses an appropriate
route; no fixed roster, provider or gateway is required. The internal battery
retains its round requirements.

**Scope and collection.** Optional external code review applies to code
reviews, using the same `"$IDH_ROOT/scripts/prose_predicate.py"` verdict as
phases 2–4. Skip these code-review routes on prose panels.
If selected, route reviews concurrently with phases 2–4 and collect completed
evidence before the result within the run's deadline. Record the actual reviewer,
route, independence basis, exact reviewed revisions and raw report. A dispatch
is not completion; a changed head requires current review evidence.

**Disposition.** Pass `verifiable:` / `consider:` findings and their supporting
evidence in the result as panel comments. `/verify-gate` dispositions external findings
identically to internal ones: only verifiable-class findings may bounce;
suggestions are noted-not-blocking. Optional participation does not waive a
returned finding.

**Panel integrity.** No suitable reviewer, a timeout or a failed route is a
visible limitation. WARN and continue the required internal battery;
optional external review is fail-open. Preserve `SEAT-FAILED:` /
`SEAT-MISSING:` records and the `PANEL-INTEGRITY:` headline verbatim in the
`/gaze` comment's panel section. These are coverage records, not findings to
disposition. Distinguish a completed clean review from absent evidence; an
unavailable route must never be reported as independent agreement. Record
external review as not selected when none was requested or attempted.

**Forge automated reviewer** (ticket 0206): `/verify-gate`'s comment-validation
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

### 6. Return the review result

Gaze ends here; it runs no gate. Read the phase outputs and return:

```yaml
result: REVIEWED | FINDINGS | ESCALATE
reviewed_head_sha: <full SHA read from the review worktree after phase 5>
unresolved_review_comments: [...]
unresolved_simplify_findings: [...]
adherence: PASS | FAIL (<n blocking>)
panel_integrity: COMPLETE | DEGRADED — <PANEL-INTEGRITY: line>
battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> | skipped (un-reviewable) | skipped (--force-approve)
circuit_breaker: un-reviewable | waived (...) | none
multi_ticket: <distinct close-claim IDs> | none
next: REVIEWED or FINDINGS → the caller fixes any FINDINGS, then runs /verify-gate <pr-number> repo=<caller's checkout> on reviewed_head_sha; ESCALATE (including battery: NOT-RUN or skipped (--force-approve)) → no gate: the caller resolves the cause or re-runs /gaze, else the author decides
```

- `ESCALATE`: the breaker fired, the battery could not run (`battery: NOT-RUN`),
  any phase 2–5 errored or timed out, or the workspace could not be restored.
  `--force-approve` is ESCALATE too, with `battery: skipped (--force-approve)`:
  nothing was reviewed (§ `--force-approve`).
  The review did not complete: the caller runs no gate and the PR goes to the
  author.
- `FINDINGS`: any blocking adherence violation, any `request-changes` or
  `major` review verdict, any unresolved `verifiable:` minor, any simplify
  must-fix not applied. List them; the caller fixes (a coder on the PR
  branch, scoped to the list) and re-runs gaze or goes straight to the gate.
- `REVIEWED`: none of the above. It is not an approval: `/verify-gate` still
  checks every exit criterion and review comment against the diff.
- `panel_integrity: DEGRADED` is a note on the result, not a fourth value: the
  result follows the rules above, and the `PANEL-INTEGRITY:` line is carried
  verbatim in the result comment.

Post the result as one PR comment (§ Output shape), then run the
cleanup and containment (§ Cleanup and containment) before returning.

**Attribution (ticket 1151).** After each review seat returns, the controller
appends that seat's `reviewer: step=review` line (with its `finding:` lines) to
the PR body through `attribution_record.py --append-pr <pr> --append '<lines>'`
(`$IDH_ROOT/scripts/`). Seats never edit the body; a failed append is reported,
not skipped.

## Cleanup and containment

On every exit path remove this run's review scratch and the review worktree, then check the containment postcondition (cwd, branch, foreign files) and report it before returning control.

## Review scratch cleanup

On every exit path (REVIEWED, FINDINGS, ESCALATE, circuit-breaker abort), after the review panel has consumed its artifacts, remove this
run's review scratch before removing the worktree.
The `/review-pr` run leaves the panel for this step. Do not run
this while perspective agents are still writing: cancel or wait for them first.
If the review worktree was never created, there is nothing to clean up. The
exit preflight must pass after scratch removal: if it reports other WIP, leave
the review worktree registered and surface those file names as ESCALATE to the
caller. Never force-remove a tree with real uncommitted files. A failed
preflight or normal worktree removal is a cleanup failure, not a successful
terminal result.

```bash
review_tree="$primary_root/.claude/worktrees/review-<pr-number>"
if [ -d "$review_tree" ]; then
    # Read verdicts before deleting panel files. Citation or ancestry uncertainty
    # keeps both the candidate .tmp and its review evidence in place.
    if [ -e "$review_tree/.tmp" ] || [ -L "$review_tree/.tmp" ]; then
        python3 "$IDH_ROOT/scripts/worktree-tmp-guard.py" removal \
            "$primary_root" "$review_tree" --branch "$PR_BRANCH" || exit 1
    fi
    tracked_panel=$(git -C "$review_tree" ls-files -- ".panel/<pr-number>") || exit 2
    tracked_base=$(git -C "$review_tree" ls-files -- build/panel-head) || exit 2
    [ -n "$tracked_panel" ] || rm -rf -- "$review_tree/.panel/<pr-number>"
    if [ ! -L "$review_tree/build" ] && [ -z "$tracked_base" ]; then
        rm -rf -- "$review_tree/build/panel-head"
    fi
    rmdir -- "$review_tree/.panel" 2>/dev/null || true
    # Detached review trees without provable branch ancestry retain .tmp.
    if ! "$IDH_ROOT/scripts/worktree-exit-preflight.sh" --removal --branch "$PR_BRANCH" "$review_tree"; then
        echo "/gaze cleanup blocked: real WIP remains in $review_tree" >&2
        exit 1
    fi
    git -C "$primary_root" worktree remove "$review_tree" || exit 1
fi
```


## Containment postcondition

On **every** exit path (REVIEWED, FINDINGS, ESCALATE, circuit-breaker abort), after removing the review worktree and before returning control to
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
  contamination in the result comment. Do not leave them for a later
  `git add` to sweep.
- **Unexpected branch** → switch back to the entry branch and flag it. Never
  end the skill with the session worktree on a different branch than it was
  on at phase 1. This runs right after the review forks return, so the shell
  cwd may sit in a foreign worktree: confirm the tree first
  (`git rev-parse --show-toplevel` should equal the session worktree), then
  anchor the corrective switch — `git -C <session-worktree> switch <entry-branch>`,
  not a bare `git switch` against an assumed cwd (rules/git.md § anchor across
  a forked-skill boundary).
- Anything that cannot be restored cleanly → downgrade the result to
  ESCALATE; a contaminated workspace must not feed a merge.

## Circuit breakers

- Close claim names a ticket file that does not exist (neither `tickets/<id>-*.erg`
  nor `tickets/closed/<id>-*.erg`; a caller may close before gating) → ESCALATE. A PR with
  no ticket at all is not a breaker.
- `pr_files >= 15` (content-bearing files, phase-1 rule) without a waiver → ESCALATE as
  `un-reviewable` before the review; this is the `rules/workflow.md` 15+ file
  monster threshold. Name the breaker in the comment and mention `multi_ticket`
  when multiple close claims add a decomposition signal. A waiver
  (`--waive-breaker` or the PR-body `Review-scope: indivisible` line, § Waiver) lifts only this stop. `--force-approve` can
  override it loudly, without review.
- Any of phases 2–5 errors or times out → ESCALATE (do not silently skip).
  Exception: simplify intentionally skipped when adherence is blocking.
- Telemetry thresholds (`## Telemetry`).

On **every** exit (not only ESCALATE) run § Cleanup and containment before
returning, so the main repo is never left in a partial state.

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

- `--force-approve` returns `result: ESCALATE` with `battery: skipped (--force-approve)`;
  nothing is reviewed, so REVIEWED is unavailable. The PR comment carries
  `/gaze: force-approved — reason: <reason>` and `FORCE-APPROVED by <reason>`.
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

next: REVIEWED or FINDINGS → the caller fixes any FINDINGS, then runs /verify-gate <pr-number> repo=<caller's checkout> on reviewed_head_sha; ESCALATE (including battery: NOT-RUN or skipped (--force-approve)) → no gate: the caller resolves the cause or re-runs /gaze, else the author decides

telemetry: risk_band=<high|low|normal> wall=<seconds>s agents=<n> tokens=<in+out> cost~=$<usd>
```

On `--force-approve`, the comment is annotated `FORCE-APPROVED by <reason>`.

## Not in scope

- **Gating.** `/verify-gate` rules APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR.
- **Fixing.** A coder on the PR branch acts on `FINDINGS`; gaze only commits phase 5 simplify fixes.
- **Wave-level integration review.** Post-merge integration review of a batch is `/roar` step 8.
- **Merging.** Ever. That is the caller's job.
