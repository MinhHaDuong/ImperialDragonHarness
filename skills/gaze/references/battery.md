# Gaze — phases 2–5 review, simplify and external panel

Loaded from `skills/gaze/SKILL.md` § 2–5.

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
or reports that the Agent tool is unavailable or a spawn failed after its one
retry, gaze does not
substitute its own sequential review: it records the failure, marks the review
unresolved and claims no completed review round. Carry the exact
`PANEL-INTEGRITY:` line the skill posted (`PANEL-INTEGRITY: DEGRADED — Agent
tool unavailable or spawn failed; selected perspectives not run`, or `missing
perspective report: <name>` for a perspective still missing at the bounded collection deadline of its one retry, phase 6) and its `dissent: unavailable` into the /gaze result comment, and use
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
