# Gaze — phases 2–5 review, simplify and external panel

Loaded from `skills/gaze/SKILL.md` § 2–5.

### 2–4. Read-only review fan-out (parallel)

These phases run as **Agent-spawned sub-agents, not `context: fork`
invocations** (ticket 0216). A fork does not inherit this skill's cwd or
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
- imperatively embeds the sub-skill's operating procedure (the steps below),
  except Agent A, which invokes the live adherence contract as specified below;
- ends by **returning a single structured block as its final message**, which
  the orchestrator parses to branch.

Spawn the applicable agents **in a single message, as parallel background
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
Invoke it directly with the review worktree; it owns its perspective
fan-out and its detached-seat substitution. There is no gaze-specific reviewer
agent: the invoking fork's own toolset supplies the delegation capability.
If review-pr itself cannot launch, record the same panel integrity failure in
the /gaze result comment, mark it unresolved, and do not claim a completed
review round.
Before launching perspectives, Agent C checks that the `Agent` tool is in its
own available toolset and that a spawn call succeeds. A missing tool, depth
limit, or denied spawn is a panel integrity failure, not permission to replace
independent perspectives with sequential self-review. Write the selected roster
to the manifest and mark each unlaunched perspective `no report`. Post the
review on the PR with `PANEL-INTEGRITY: DEGRADED — Agent tool unavailable or
spawn failed; selected perspectives not run` and `dissent: unavailable`;
return those same lines in Agent C's structured block. The /gaze orchestrator
must carry the exact `PANEL-INTEGRITY:` line into its final verdict comment
and use `panel integrity: DEGRADED` in the actions section. Never write
`dissent: none` for this path. When Agent C's own toolset lacks the
`Agent` tool, apply the detached-seat substitution in
skills/review-pr/SKILL.md instead of degrading.
If a launched perspective is still missing at the bounded collection deadline,
name it as `no report`, post and return `PANEL-INTEGRITY: DEGRADED — missing
perspective report: <name>`, and use `dissent: unavailable` there too.
**Width-gate:** run Agent C on every PR. For round-1 code diffs, read
`$IDH_ROOT/skills/review-pr/panel-width.json` and apply its
`max_lines`, `max_files`, and `pipeline_paths` to `git diff --numstat
--no-renames origin/<base>...HEAD` in the review worktree. A diff within both
limits and with no pipeline path gets Correctness only. A binary count, missing
base, or unreadable config selects the proportional panel, with at least
Correctness + Consistency even if the risk description is trivial. `review:standard`
in the PR label/body or linked ticket body selects all five code perspectives
even for a tiny diff. A Correctness reviewer concern or low confidence adds
the other four perspectives before synthesis. when the merge request already carries a prior Agent C
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
Otherwise route by the shared prose predicate, anchored in the review
worktree — the predicate reads the disk (manifest walk-up, `\documentclass`
sniff), so a parked cwd would return a plausible, wrong verdict, the failure
mode this ticket exists to close. Run
`cd $primary_root/.claude/worktrees/review-<pr-number> && python3 "$IDH_ROOT/scripts/prose_predicate.py" <changed files>`
— it prints `prose` when any changed file resolves to a `doctype` (from the
project's `.claude/rules-map.toml` manifest, else the `\documentclass`
sniff; one manuscript flips a mixed diff), `code` otherwise. It refuses any
path that does not exist under that cwd (exit 2, no verdict) — treat a
refusal as a routing error to fix, never as `code`. Process prose — notes,
tickets — carries no doctype and stays on the code panel, which is the panel
the audit measured as correct for it (ticket 0550). Spawn a read-only Agent on the review worktree `$primary_root/.claude/worktrees/review-<pr-number>`
(all git via `git -C`), whose embedded procedure is: read the linked ticket's exit criteria and the
diff, assess risk, apply the Width-gate for round-1 code, and run the selected
perspective set in parallel —
**code:** correctness, consistency, scope, red-team, doc-propagation (trivial →
correctness only when Width-gate qualifies; otherwise at least +consistency;
scripts or other pipeline paths → +doc-propagation;
substantial → all five); **prose:** discipline panel sized to the change,
always including an adversarial referee and an AI-tells auditor that scans the
full text against `config/ai-tells.yml`. Each perspective reports
confidence and a verdict (approve / comment / request-changes for code; accept
/ minor / major for prose).
If the round-1 code panel was reduced to Correctness only and that reviewer
raises a concern or low confidence, add the other four perspectives and
collect their reports before synthesis. An explicit `review:standard` request
also forces all five code perspectives. Synthesize: preserve dissent verbatim,
dedupe, and run the project's declared gate. With `.idh-checks.json`, use
`python3 "$IDH_ROOT/scripts/scoped-check.py"` and carry `selected:` and `skipped:`
into the review; without a map, run `make check`. A scoped pass is not a full
gate claim. Every non-blocker (minor) finding **must** carry exactly one tag
prefix — `verifiable:` (a reproducible failing assertion is attached),
`consider:` (hypothesis, no enforcement), or `nofollow:` (noted, not pursued);
hedged "might break X" phrasing is forbidden — produce the assertion or
downgrade to `consider:`. Blockers (request-changes / major) are untagged.
Post the single review on the PR and return the synthesized findings (blockers
+ tagged minors) as the structured block. This inner panel is itself a fan-out:
Agent C must launch its perspective agents in one message, each writing its
own artifact, and poll those artifacts until every one has landed
returns before it synthesizes — the fork contract applies recursively (see
**Fork execution contract**; ticket 0263, `/gaze 479`, 2026-07-11). Embed in
its prompt the 30-second live-state polling rule above; if the PR stops,
cancel its perspective agents and return the phase/state line without posting
a review.

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
weakens the phase. Existing tiny/prose/adherence skips above remain unchanged.

## External reviewer panel

External, decorrelated review is optional evidence routed by the active
runtime. When useful or requested, describe the expertise, capability and
independence needs through `skills/reviewers/SKILL.md` and read its live-route
reference. The runtime discovers available reviewers and chooses an appropriate
route; no fixed roster, provider or gateway is required. The internal battery
retains its round requirements.

**Scope and collection.** Optional external code review applies to small/full
CODE reviews, using the same `"$IDH_ROOT/scripts/prose_predicate.py"` verdict as
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
