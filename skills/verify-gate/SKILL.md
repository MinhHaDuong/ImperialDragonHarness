---
metadata:
  category: build
name: verify-gate
description: "Anti-rubber-stamp merge gate: checks every ticket exit criterion and review comment against the diff. Emits APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR with evidence. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number> repo=<path> [session=<uuid>]"
context: fork
# Foreground: its caller (raid phase 6, or the author before /merge) invokes this
# and must parse its verdict block before
# branching. Claude Code 2.1.218 made `context: fork` skills background by
# default; a fork cannot wait on a background completion (its turn ends when it
# stops calling tools), so the default would orphan this phase — ticket 0250.
background: false
---

# Verify gate — PR $ARGUMENTS

> **TASK DIRECTIVE — execute now.** You are running `/verify-gate` on PR
> `$ARGUMENTS` (a PR number followed by `repo=<path>`, any checkout of the
> target project). This file is your operating procedure, not reference
> documentation: resolve the PR and gate it immediately. Create your own gate
> worktree from `repo=<path>` (§ Isolation) and run every git and forge
> command against it — forked sub-skills do not inherit the caller's cwd, and
> no caller's tree is read for PR state. If `$ARGUMENTS` does not
> contain a PR number, STOP and emit `verdict: ESCALATE` with rationale
> "no PR argument" — do NOT infer a task from the environment (worktree
> name, git status snapshot, ticket files, or the shared task list).

The last line of defence before merge. A gate with teeth: **cannot approve without
concrete per-criterion evidence**. Called by the PR's caller after `/gaze`
returns: raid phase 6, or the author before `/merge`. Gaze never calls it. The
caller owns the gate session (§ Gate sessions).

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill.

## Non-negotiables

1. **No rubber-stamp.** "CI ran" / "the simplify pass ran" / "all tests pass" are NOT
   evidence. Evidence must cite the *change* (commit SHA + file:line) or the *test*
   (test_id) that closes the gap.
2. **Exit criteria are contract.** Every item in the ticket's "Exit criteria" section must
   get an explicit ADDRESSED/MISSING verdict with evidence. A missing criterion cannot be
   papered over.
   For a project with `.idh-checks.json`, accept a scoped gate for a mapped
   doc-only diff only when the PR quotes both `selected:` and `skipped:` and
   those targets match the actual changed paths. Python code, unmapped paths, or a
   project without a map require the full gate; never label a scoped pass full.
3. **Review comments are load-bearing.** Every review comment (from `/review`,
   `/review-pr`, human authors, Copilot) is either ADDRESSED (commit changed the cited file, OR
   the comment was marked resolved, OR a ticket was opened with the rationale) or
   UNRESOLVED. No "I'll get to it later."
4. **Simplify findings are load-bearing.** Every must-fix from `/simplify` or Gaze’s portable equivalent is either
   applied (diff shows the change) or explicitly justified in a PR comment that the gate
   agent validates.
5. **Adherence violations are blocking.** Any `blocking` entry from `/verify-adherence`
   is a REROLL trigger.
6. **Two rounds max.** Round 1 is initial gate. Round 2 is post-fix re-gate. Round 3 is
   forbidden — escalate.
7. **Tagged minors are mandatory.** Review comments from `/review-pr` and
   `/review-pr-prose` at the minor/suggestion tier must carry one of `verifiable:`,
   `consider:`, or `nofollow:`. Untagged minors and ambiguous "X might break" /
   "this could cause Y" phrasings are refused — the gate does not triage hedges. See
   "Minor tag handling" below.

## Input

Either:
- `<pr-number>` alone: the gate resolves ticket, diff, comments itself.
- The caller's bundle (preferred): `/gaze`'s returned result block
  (`reviewed_head_sha`, unresolved lists, adherence, panel integrity), with
  `{pr, ticket}`.
- The waiver record `/gaze` returned, passed on by the caller, when one exists: `waiver: none`, or the declared
  reason, `pr_files`, `pr_lines`, the source (`flag` or `body line`), and the earliest
  posted `circuit_breaker: waived (...)` header on the PR. The gate judges the claim
  from the diff, not from who declared it (see § Indivisibility).

Both paths produce the same verdict shape. Round is always derived from PR comment
history (see § Gate sessions), never passed by the caller.

**Cwd prerequisite**: the gate uses `gh` and `git` commands that resolve
against cwd, and a `context: fork` invocation does **not** inherit the
caller's cwd. The caller passes `repo=<path>`, any checkout of the target
project that the caller keeps until the gate returns (its session or PR
worktree). The gate uses it only to locate the repository, never to read PR
state: whatever branch is checked out there is irrelevant.

**Isolation — the gate owns its checkout.** Every invocation, whoever the
caller, creates a fresh detached worktree on the PR head, rules from it and
removes it on exit. No caller hands the gate a tree, and the gate never reads
a tree another skill created: `/gaze` removes its review worktree before it
returns, so a later gate run cannot rely on it.

```bash
PR_BRANCH=<head branch resolved from the forge for <pr-number>>
primary_root=$(git -C "<repo-path>" rev-parse --show-toplevel) || exit 1
primary_root="${primary_root%%/.claude/worktrees/*}"
gate_tree="$primary_root/.claude/worktrees/gate-<pr-number>"
git -C "$primary_root" fetch origin "$PR_BRANCH" || exit 1
if ! git -C "$primary_root" worktree add --detach "$gate_tree" origin/"$PR_BRANCH" || ! test -d "$gate_tree"; then
    echo "verify-gate: cannot create isolated gate worktree for PR <pr-number>" >&2
    exit 1   # verdict ESCALATE, root_cause_class: Missing Data
fi
```

On every exit path, after the verdict comment posts: `git -C "$primary_root"
worktree remove "$gate_tree"`. The gate writes nothing in it, so a plain
remove suffices; a refusal is reported in the verdict, never forced.

## Evidence discovery

For each ticket exit criterion, the gate searches:

- **Commit messages** on the PR branch for the criterion's key phrases.
- **Diff** for files the criterion mentions (scripts, tests, docs).
- **Test suite** for test IDs that match the criterion's verification claim.
- **PR body** for explicit statements with references.

A criterion cannot be ADDRESSED solely on "the PR says so." Either a commit touched the
relevant file, or a test exists that covers the behaviour, or a rationale is posted.

For each review comment, the gate searches:

- **Commits made AFTER the comment timestamp** for changes to the commented file/line.
- **Comment resolution status** (forge's resolved/outdated flag, where available).
- **Reply threads** for author acknowledgment + follow-up ticket reference.

A comment is UNRESOLVED if none of the above applies.

## Review evidence

Seat reports are repository files under `tickets/reviews/<base>..<head>/`, one
per seat execution, written by the controller with
`review_evidence.py record`. The gate never reads a seat's verdict from prose.
Run the three steps sequentially: the plan line decides whether steps 2 and 3
apply, and step 2 needs its seats.

1. **Plan.** Read the review plan line hunt keeps in the merge-request body:
   `Review plan: risk=<trivial|ordinary|high> seats=<seat>,<seat> producer-family=<family>`.
   Without a plan line and without any report on the branch, record
   `review_evidence: legacy` and judge the review comments as above; stop here.
2. **Seat table.** In the gate worktree, run
   `python3 "$IDH_ROOT/scripts/review_evidence.py" gate --repo "$gate_tree" --base origin/<base-branch> --ticket <ticket-file> --risk <row> --producer-family <family> --seat <seat>` (one `--seat` per planned seat).
   Copy its `seat`, `independent`/`independence` and `risk` lines into the
   verdict. A seat is `ran` (report on this head), `reused` (same patch-id,
   criteria hash and policy version, from an earlier head, which it names),
   `stale` or `no-report`. Check, gate and adherence results are never reused:
   they always re-run on the delivered head. The high row adds `red-team` and
   requires one seat from another family than the producer's.
3. **Forge reviews.** Run
   `python3 "$IDH_ROOT/scripts/review_evidence.py" forge <owner/name> <merge-request>`.
   It reads reviews, conversation comments and inline review-thread comments
   (with their resolved flag). Only the pinned actors are admitted, and only
   unedited: rows read `human: ran` or `copilot: ran`. These are binding
   comments under non-negotiable 3, never seats, never reused, never counted
   toward independence. Exit 0: every row admitted. Exit 1: at least one
   `rejected` row (unknown actor, edited or edit status unknown); it never
   counts as proof, and its findings still bind like any other comment.
   Exit 3: the forge read failed or came back truncated (more than one page),
   so the comment set is unknown: `Missing Data`, ESCALATE.

## Scope containment

After verifying exit criteria (completeness), the gate checks containment:
does the diff include work not attributable to any exit criterion?

Inspect the branch with `git log origin/main..origin/<branch> --stat` (two-dot,
never three-dot — three-dot is symmetric difference and catches unrelated commits
pushed to main during the raid). For each changed file, trace it to an exit
criterion or a necessary dependency (e.g., a test file for a new function).

The gate reports findings in the `scope_overflow` section of the verdict. It does
not create tickets or edit the PR body — the caller handles disposition.

Never rebase or amend commits to excise scope creep.

**Comment-only hunks never block.** A hunk confined to comments (LaTeX `%`, code
comments, Markdown/HTML comments) is never a scope or authorisation blocker, even
under a path the brief marked protected (e.g. "do not edit `rapport/`"): record it
as a `nofollow:` minor, no `scope_overflow` entry. Typeset text and argument
changes keep the guard.

## Verdict shape

```yaml
verdict: APPROVED | REROLL | ESCALATE | NEEDS-AUTHOR
round: 1 | 2
pr: <pr-number>
ticket: <ticket-id>
waiver: none | {reason, pr_files, pr_lines, source}
per_exit_criterion:
  - criterion: "<verbatim>"
    status: ADDRESSED | MISSING
    evidence: "<commit SHA + file:line | test_id>"
unresolved_review_comments:
  - comment_ref: <url|id>
    author: <login>
    tag: verifiable | consider | nofollow | untagged
    why_unresolved: "<reason>"
malformed_minors:
  - comment_ref: <url|id>
    excerpt: "<hedged phrasing>"
unresolved_simplify_findings:
  - finding: "<verbatim>"
    severity: must-fix | nice-to-have
    status: NOT_APPLIED | WAIVED_WITHOUT_RATIONALE
unresolved_adherence_violations:
  - rule_ref: "<.claude/rules/foo.md#bar>"
    file: <path>
    severity: blocking | nit
scope_overflow:
  - file: <path>
    reason: "<not traceable to exit criterion>"
    suggested_disposition: TICKETED | ESCALATE
review_evidence: legacy | {seats, independence, risk, forge}
  # seats: "seat <name>: ran|reused|stale|no-report (<verdict>) - <reason> <report>"
  # independence: "independent: <family> seat <name>[, inherited from <head>]" or "missing"
  # risk: "risk: <plan row> / floor: <floor row>"
  # forge: "human: ran <login> ..." | "copilot: ran <login> ..." | "rejected <login> ... (<reason>)"
rationale: |
  <strongest remaining reviewer attack; if APPROVED, why evidence holds>
root_cause_class: Agent Error | Extractor Error | Original Error | Missing Data | Other  # required on REROLL/ESCALATE
reroll_bump: note verify-reroll — round {n}: {top unresolved criterion}  # only if REROLL — the gate writes nothing; the orchestrator poses this line
second_round_needed:   # only if REROLL
  - <prioritised items from unresolved lists>
```

## Indivisibility (recorded waiver)

Runs only when the waiver record is not `none`. A waiver lifts the un-reviewable
file-count stop for a change that cannot be split. The gate judges the claim from
the diff alone, as one `per_exit_criterion` row named `indivisibility waiver`:

- **Reason holds.** Every changed file is a pure rename or a rewire of a reference
  to a renamed path or symbol, and no changed file carries an independent change
  that could land alone (a fix, a feature, a separate content edit). Cite the
  classified files as evidence. A file that could land alone is MISSING, with its
  file:line.
- **Size.** The growth baseline is the earliest posted `circuit_breaker: waived (...)`
  header on the PR, not the phase-1 recount of this round (a recount absorbs the
  growth it should catch). The verdict-time `pr_files` and `pr_lines` must not exceed
  that baseline. Growth past it makes the PR un-reviewable: the verdict is
  `circuit_breaker: un-reviewable` and ESCALATE.
- **Multi-ticket.** Two or more close claims beside a waiver are recorded as
  `multi_ticket` with a non-blocking disposition, as in the preflight.
- **Verdict.** A waiver never yields APPROVED. When every other criterion passes and
  the indivisibility row is ADDRESSED, the verdict is `NEEDS-AUTHOR`: the author
  decides whether to merge. A MISSING row follows the usual REROLL / ESCALATE rule.

## Decision rules

- Any `MISSING` in `per_exit_criterion` → REROLL (round 1) / ESCALATE (round 2).
- Any `UNRESOLVED` review comment from a human author → REROLL (round 1) / ESCALATE (round 2).
- Any `UNRESOLVED` review comment from `/review-pr` labelled severity ≥ medium →
  REROLL (round 1) / ESCALATE (round 2).
  Severity triggers apply to blockers (request-changes). Tagged minors are triaged by tag, not severity.
- Any unresolved `verifiable:` minor (failing assertion still reproduces) → treated as
  blocker-adjacent: REROLL (round 1) / ESCALATE (round 2).
- `consider:` minors are informational. They appear in the verdict comment but do not
  bounce the PR. Author is free to ignore.
- `nofollow:` minors are muted. The gate records them for the audit trail and does
  nothing else.
- Any `NOT_APPLIED` must-fix simplify finding without rationale → REROLL (round 1) /
  ESCALATE (round 2).
- Any `blocking` adherence violation → REROLL (round 1) / ESCALATE (round 2).
- Any `stale` seat, a missing other-family seat at the high row, or a plan row
  below the risk floor → REROLL (round 1) / ESCALATE (round 2).
- Any planned seat with `no-report` → ESCALATE. There is no merge with a recorded gap.
- A seat that ran or was reused with verdict `changes` keeps its findings
  load-bearing: they follow the review-comment rules above.
- Any `scope_overflow` entry with suggested disposition ESCALATE → ESCALATE.
- A recorded waiver whose `indivisibility waiver` row is MISSING → REROLL (round 1)
  / ESCALATE (round 2), as any MISSING criterion. Growth past the earliest posted
  waived size → ESCALATE (un-reviewable).
- A recorded waiver with the indivisibility row ADDRESSED and every other list empty
  → NEEDS-AUTHOR, never APPROVED.
- A PR with `pr_files >= 15` content-bearing files and no waiver record → ESCALATE
  (un-reviewable), counted by the gate itself on every invocation path.
- `scope_overflow` entries with all suggested dispositions TICKETED → does not block
  APPROVED. Caller handles ticket creation and PR annotation.
- All lists empty AND all criteria ADDRESSED, with no recorded waiver → APPROVED.

**On REROLL**: write no ticket file — run no `erg log`, ever. Emit the bump line
in the verdict as a `reroll_bump:` field: `note verify-reroll — round {n}: {top unresolved criterion}`.
The gate runs in an isolated checkout over a shared `main`; a mid-wave `erg log`
on the ticket collides at the insertion point with the branch's own ticket
commits. The orchestrator poses the line: committed onto the PR branch with the
REROLL fix, or deferred to merge time.
For a `/verify-gate` invocation outside raid, its caller owns posing
the returned `reroll_bump` by the same rule: on the PR branch with the fix, or
at merge time. The caller never runs `erg log` against main mid-wave; the gate
still writes no ticket file.

If `round == 2` and any trigger fires → upgrade to ESCALATE. Never a third round.

## Root-cause taxonomy

Every REROLL or ESCALATE verdict carries a `root_cause_class` — a shared label
for *why* the gate is bouncing (source: arXiv:2604.21965 §5.3, reframed for the
harness). This is a labeling convention, like the minor tags, not a
mechanical detector; assign it when you author the verdict.

- **Agent Error** — the implementer misread the ticket or a rule. E.g. wired
  `make check-fast` where the ticket asked for `make lint`.
- **Extractor Error** — the ticket was underspecified. E.g. "document the
  taxonomy" without naming which file it belongs in.
- **Original Error** — a pre-existing bug the gate surfaces, unrelated to this
  diff. E.g. a broken test the branch merely runs into.
- **Missing Data** — the gate lacked context or access. E.g. `repo=` not
  passed or the gate worktree could not be created, so the diff could not be
  inspected.
- **Other** — none of the above; state the reason in `rationale`.

APPROVED verdicts do not carry this field.

## Minor tag handling

Tag definitions live in `/review-pr` (canonical source). Gate treatment:

- `verifiable:` → blocker-adjacent. Unresolved → REROLL.
- `consider:` → informational, surfaced but never bounces.
- `nofollow:` → muted, not surfaced.

Untagged minors go in `malformed_minors`; they do not bounce on their own.
On round 2 any untagged minor still present → ESCALATE.
The gate never authors hedged language — use `verifiable:` or `consider:`.

## Gate sessions

The caller owns the gate session; gaze has no part in it.

- **Session id.** Before round 1 the caller generates one UUID for the PR's
  gating sequence (`python3 -c 'import uuid; print(uuid.uuid4())'`) and passes
  it as `session=<uuid>` on round 1 and on the round-2 re-gate after the fix.
  Raid generates it per PR in phase 6; the author generates it before `/merge`.
- **Standalone** means only that no `session=` was passed (an author's ad hoc
  or debugging run): the gate generates a fresh UUID and records it. It changes
  no rule below; there is no standalone override.
- **Round derivation:** count PR comments matching `/verify-gate round=N verdict=V`,
  across every session and caller; current round = count + 1. The caller never
  passes the round.
- **Two-round cap, every path.** Round > 2 → immediate ESCALATE, whoever calls
  and whether or not a session id was passed. A fresh session id does not reset
  the count. Past an ESCALATE the merge decision is the author's, not another
  gate run's.
- **Caller enforcement.** The caller invokes the gate at most twice per
  session: round 1, then one re-gate after the fix. Raid never launches a
  third run and never opens a new session to escape the cap.

Uses existing PR state only when no gaze result is passed (no phase 2-5 outputs).
Isolation is the same on every path (§ Isolation: own worktree, removed on exit).

## Output destinations

1. Structured verdict returned to the caller (raid, or the author).
2. PR comment posted with human-readable summary:

   Take the `gate_session_id` from the caller's `session=` argument; with
   none (standalone), generate a fresh UUID. The review worktree path is the gate's
   own `$gate_tree`. Immediately before ruling, read the full tip SHA with
   `git -C "$gate_tree" rev-parse HEAD`; stop with ESCALATE if this fails.
   These are audit fields.

   ```
   /verify-gate round=<n> verdict=<V>
   Gate session id: <UUID from the caller's session=, or standalone UUID>
   Review worktree path: <absolute path of the gate's own worktree>
   Ruled tip SHA: <full commit SHA read from that worktree>
   reroll_bump: <exact returned note verify-reroll line; include on REROLL, omit otherwise>
   Exit criteria: <addressed>/<total>  Review: <unresolved>  Simplify: <unresolved>
   Adherence: <blocking>  Scope overflow: <files> (<ticketed>/<escalate>)
   Minors: verifiable:<n> consider:<n> nofollow:<n> malformed:<n>
   Evidence: <legacy | ran:<n> reused:<n> stale:<n> no-report:<n>>  <risk line>  <independence line>
   Top reasons (if not APPROVED): <ranked list>
   Rationale: <paragraph>
   ```

## Circuit breakers

- No ticket (no close claim, no title/body reference) → not a breaker. The
  PR body's stated intent and test plan stand in for exit criteria; record a
  `no_ticket` nit.
- A close claim naming a ticket file that does not exist → ESCALATE (dangling
  claim; `/merge` would fail on it).
- PR body lacks test plan → not a gate-level failure, but recorded as a nit.
- Gate cannot access commit timestamps → ESCALATE (cannot distinguish pre/post comment changes).
- Contradictory signals between phases 2–5 → ESCALATE (no silent resolution).
- Un-reviewable breaker: the gate counts the content-bearing files itself, from
  `git diff --name-status -M` and `git diff --numstat -M` (the phase-1 rule). When
  `pr_files >= 15` and there is no waiver record, the verdict is ESCALATE with
  `circuit_breaker: un-reviewable`. The gate does not trust the caller's count or the
  caller's omission of the breaker.
- Waived PR: when a waiver record is present, run § Indivisibility. If the
  indivisibility row is ADDRESSED and nothing else blocks, the verdict is
  NEEDS-AUTHOR, never APPROVED; a MISSING row follows the usual REROLL / ESCALATE
  rule. Growth past the earliest posted waived size → ESCALATE (un-reviewable).
- Waiver source: when the caller passes no waiver record, the gate reads it from the
  PR comments, taking the earliest posted `circuit_breaker: waived (...)` header. It
  does so on every invocation path, including the caller-side recovery and
  fork-liveness recipes in `/gaze`, so the check holds whether or not the caller
  hands the record over.

## Not in scope

- **Merging.** The gate does not merge; that decision belongs to the caller.
- **Re-running tests.** The gate reads results; phase 1 of `/verify-adherence` runs them.
- **Acting on scope overflow.** The gate detects and reports; the caller tickets and annotates.
