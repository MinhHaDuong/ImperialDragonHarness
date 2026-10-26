# Gaze — phases 2–5 review, simplify and external panel

Loaded from `skills/gaze/SKILL.md` § 2–5.

### 2–4. Read-only review fan-out (parallel)

Agent A (adherence), the panel seats of Agent C and the optional adapter seats
run as **Agent-spawned sub-agents, not `context: fork` invocations** (ticket
0216). A fork does not inherit this skill's cwd or
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
`references/panel.md`; if that also cannot run, emit a one-line
`battery: NOT-RUN — cause: <guard|no-agent-tool|depth>` in the result
comment. The boundary with the seat-level signal: no seat launched at all is
a battery NOT-RUN; seats launched but reports missing stays seat-level
`PANEL-INTEGRITY:` (whose name is unchanged). The NOT-RUN line names a launch
failure, not a review finding: never fabricate findings. The result is capped
at ESCALATE, never APPROVED (gaze returns no approval at all).

Every reviewer agent's prompt:
- opens with `TASK DIRECTIVE — execute now`, naming the single sub-skill
  procedure it runs and the PR;
- forbids `add`, commits, pushes, new branches, new PRs, and any write to
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
  specified below; the simplify reviewer gets the phase 5 steps;
- ends by **returning a single structured block as its final message**, which
  the orchestrator parses to branch.

Spawn the applicable agents (Agent A, the panel seats and any adapter seats)
**in a single message, as parallel background
Agent calls**, each writing its result to the phase artifact path — the single message runs them
concurrently, and the bounded poll on those artifacts is what makes this fork wait
before it proceeds. Keep polling until every artifact lands: a fork's
turn ends the moment it stops calling tools, and a background completion
re-invokes the MAIN loop, not the fork, so a fork that stops polling returns at
launch and orphans its reviewers (ticket 0250; see **Fork execution
contract**). Once all return, collect their structured outputs. Choose the model of each launched worker per launch, from the `route` skill grid
(`skills/route/SKILL.md`); seats that must be independent follow
`skills/route/references/decorrelation.md` ("The launch line").

Seat defaults are guidance, not pins; raise a seat when the change warrants it:

| Seat | Default worker class | When to raise |
|---|---|---|
| adherence, scope, docs-propagation, consistency | cheap cluster | a rule is subtle or the diff is large |
| correctness | cheap cluster | high-risk or cross-cutting change |
| red team | cheap cluster | high-risk change: another family (`decorrelation.md`) |


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
Skill(skill: "verify-adherence", args: "<branch> worktree=$primary_root/.claude/worktrees/review-<pr-number> semantic=caller")
```

Substitute the resolved branch and absolute review-worktree path in the args.
Pass through `trace=<path>` when the caller supplied it. Do not embed or
reimplement the verification steps here: the skill loader supplies the current
procedure, including project-runner discovery, reference resolution, and trace
checks. Wait for completion and return its structured verdict unchanged:
`adherence: PASS|FAIL`, plus `semantic_review`, `mechanical_failures`,
`semantic_findings` (each with `severity: blocking|nit`), and
`untested_rules`. Propagate ESCALATE, a timeout, or an unparseable result as
an infrastructure failure; never replace a missing verdict with PASS. Write
the result to Agent A's phase artifact using the same completion protocol as
the other reviewers.

**Gaze launches the semantic worker (ticket 1173).** `semantic=caller` keeps
the seat read-only: it returns `semantic_review.status: delegated` with the
applicability decision and `rule_sources`, and launches nothing. When that
artifact lands with `adherence: PASS` and `applicable: true`, or the changed
files include an instruction file, gaze launches one semantic worker itself, sequentially after the seat
because it needs the seat's `rule_sources`: one background subagent writing `adherence-semantic.md` under the same
artifact protocol and bounded poll, given the inputs and prompt of
verify-adherence § 3 and the seat's `rule_sources`. Choose its model from the
`route` skill. Record its observed worker id, route and launch evidence when
it starts. Then fold the two returns, always, whether or not a worker was
launched:

```
python3 "$IDH_ROOT/scripts/adherence_verdict.py" --seat <adherence.md> [--worker <adherence-semantic.md> --worker-id <id> --route <route> --launch-evidence <record> --completion-evidence <artifact path>] --changed <the PR's changed paths, always, never omitted or empty>
```

Its stdout is the adherence verdict gaze uses everywhere downstream; exit 1 is
FAIL. The script fails any instruction-file diff without a completed, valid
worker report as `adherence-infrastructure`, so a skipped phase cannot read as
PASS; that infrastructure FAIL is unresolved phase 2 and gaze ESCALATEs.
Exit 2 (unreadable seat or worker artifact, or an omitted or empty
`--changed`) is an infrastructure failure, treated like
`adherence-infrastructure` (ESCALATE), never a PASS or an ordinary FAIL. The
script reads the last yaml fence of each artifact. The early-exit reads the merged `adherence` and its count of `blocking` findings.

**Native `/review` and `/simplify`**: native `/review` is an optional adapter
seat, never the basis of the review. Native `/simplify` is not used: it applies
fixes, and phase 5 is report-only (below).

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

**Agent C — PR review** (the panel, `references/panel.md`; on a prose diff
also `references/prose-panel.md`). This is the one launch mode: gaze launches
the seats itself, as the code-reviewer or prose-reviewer profile, with the
perspectives it chose (§ 2–5); there is no separate review skill and no
gaze-specific reviewer agent.

**Route first.** Choose the panel by the shared prose predicate, anchored in the
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
the audit measured as correct for it (ticket 0550).

**Panel integrity in gaze's result.** If the seats cannot launch, the Agent tool
is unavailable or a spawn failed, gaze does not substitute its own sequential
review: it records the failure, marks the review unresolved and claims no
completed review round. Post the exact `PANEL-INTEGRITY:` line
(`PANEL-INTEGRITY: DEGRADED — Agent tool unavailable or spawn failed; selected
perspectives not run`, or `missing perspective report: <name>` for a seat still
missing at the bounded collection deadline) and `dissent: unavailable` in the
panel review and the /gaze result comment, with `panel integrity: DEGRADED`
there. Never write `dissent: none` for this path.

Wait for all spawned agents to complete. Collect their structured outputs.

**Early-exit check**: if the adherence agent returned any `blocking` violations, skip phase 5 (simplify). Blocking adherence guarantees FINDINGS; simplify tokens would be wasted. Log `simplify: skipped (adherence blocking)` in the telemetry phase line.

### 5. Simplify (sequential, report-only)

**Report-only.** Gaze makes no commits: simplify findings are reported like
panel findings, and the coder acts on them (`skills/merge/SKILL.md`
§ Before merging).

**When it runs.** Round 1: the PR carries no earlier `/gaze` result comment
whose `simplify:` line reports a pass. On a later round, run it only when the
diff grew materially since the head that pass names (new files or new
mechanisms, not the fixes to earlier findings); otherwise log
`simplify: skipped (no material growth)`. Ten passes on two PRs (ticket 1213)
applied nothing after round 1.

**Prose-skip:** when the diff routed prose (the same
`"$IDH_ROOT/scripts/prose_predicate.py"` verdict the phase 2–4 panel choice used), skip
this phase and log `simplify: skipped (prose workpackage)` in the telemetry
phase line: the prose panel already judges cuts, and a manuscript change
proposed here would still have to travel through `rules/prose/workpackages.md`
(ticket 0550). Otherwise, after 2–4 land their comments (and the early-exit
check passes), launch the reviewer.

Launch a separate reviewer through the active runtime (model chosen per launch
from the `route` skill), using the phase artifact and bounded-wait contract
above. Give it the explicit PR number, review tree, base ref, anchor HEAD and
changed-file roster. It runs the review-anchor check before and after
examining `git -C <review-tree> diff origin/<base>...HEAD` and the relevant
surrounding code or instructions, and it edits nothing. It looks for:

- unnecessary complexity, duplication, existing mechanisms to reuse, and safe
  simplifications that preserve behavior and ticket intent;
- **proportion:** lines that defend against a scenario no real actor
  produces — a theoretical race, an input no caller sends, a guard on a
  guard. For each, name the scenario, who would produce it, and what the
  defence costs (lines, branches, tests), and propose deleting it. Simplify
  that judges only hunks missed ~55 lines of lock-claim machinery the author
  deleted (ticket 1213).

This is a distinct simplification pass, not a rerun of a general
review. It returns the reviewed SHA, paths examined, and actionable
findings with severity (`must-fix` or `consider`), location, proposed change
and rationale; or a CLEAN verdict explaining the concrete candidates
considered and why they need no change. An absent reviewer, timeout, anchor
mismatch, wrong diff or missing evidence means this phase is unresolved and
triggers the existing breaker.

Feed all findings (or the evidenced CLEAN result) and the reviewed SHA into
the result as `unresolved_simplify_findings`. A must-fix is resolved by a
coder fix on a later head or a justified disposition in a PR comment, which
`/verify-gate` rule 4 checks.

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
evidence before the result within the run's deadline. Run a headless CLI reader
(`codex exec`, `claude -p`, `pi -p`) through
`python3 "$IDH_ROOT/scripts/seat_clock.py" run --cap 600 --out <panel>/<name>.md -- <cli...>`:
it is killed at the cap and its line, `reported in <s>s` or `no report (timed
out after 600s)`, goes in the result's `seat times:` line; on `no report` WARN,
continue and say so. Record the actual reviewer,
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
