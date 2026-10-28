---
metadata:
  category: build
  order: 4
name: verify-gate
description: "Anti-rubber-stamp merge gate: checks every ticket exit criterion and review comment against the diff. Emits APPROVED / REROLL / ESCALATE / NEEDS-AUTHOR with evidence. Does not merge."
disable-model-invocation: false
user-invocable: true
argument-hint: "<pr-number>|branch:<name> [base=<ref>] repo=<path> [session=<uuid>] [integration]"
context: fork
# Foreground: its caller (raid phase 6, or the author before /merge) invokes this
# and must parse its verdict block before
# branching. `context: fork` skills may default to background; a fork cannot
# wait on a background completion (its turn ends when it stops calling tools),
# so the default would orphan this phase.
background: false
---

# Verify gate — PR $ARGUMENTS

> **TASK DIRECTIVE — execute now.** You are running the verify-gate skill on PR
> `$ARGUMENTS` (a PR number followed by `repo=<path>`, any checkout of the
> target project). This file is your operating procedure, not reference
> documentation: resolve the PR and gate it immediately. Create your own gate
> worktree from `repo=<path>` (§ Isolation) and run every git and forge
> command against it — forked sub-skills do not inherit the caller's cwd, and
> no caller's tree is read for PR state. A forge-less project names the
> unit `branch:<name> [base=<ref>]` in place of the number (§ Notes review).
> If `$ARGUMENTS` contains neither, STOP and emit `verdict: ESCALATE` with rationale
> "no PR argument" — do NOT infer a task from the environment (worktree
> name, git status snapshot, ticket files, or the shared task list).

The last line of defence before merge. A gate with teeth: **cannot approve without
concrete per-criterion evidence**. Called by the PR's caller after gaze
returns: raid phase 6, or the author before `/merge`. Gaze never calls it. The
caller owns the gate session (§ Gate sessions).

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins.

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
   the findings of every gaze answer on notes (§ Notes review), human authors, Copilot) is either ADDRESSED (commit changed the cited file, OR
   the comment was marked resolved, OR a ticket was opened with the rationale) or
   UNRESOLVED. No "I'll get to it later."
4. **Simplify findings are load-bearing.** Every must-fix from Gaze’s report-only simplify
   phase is either fixed by the coder (diff shows the change) or explicitly justified in a
   PR comment that the gate agent validates. Read the `Unresolved simplify:` line of every
   gaze answer of the review (`review_notes.py show`): a later round may have skipped simplify.
5. **Adherence violations are blocking.** Adherence is read from the merge
   gate record's checks (`lint` runs the `-m adherence` tests; § Check
   plan), never from a gaze result: a failing check is a REROLL trigger.
6. **Two rounds max.** Round 1 is initial gate. Round 2 is post-fix re-gate. Round 3 is
   forbidden — escalate.
7. **Tagged minors are mandatory.** Review comments from the gaze code and
   prose panels at the minor/suggestion tier must carry one of `verifiable:`,
   `consider:`, or `nofollow:`. Untagged minors and ambiguous "X might break" /
   "this could cause Y" phrasings are refused — the gate does not triage hedges. See
   "Minor tag handling" below.

## Input

Always `<pr-number> repo=<path>`. Without `repo=`, STOP and emit
`verdict: ESCALATE` with rationale "no repo argument": a fork has no cwd to
fall back on. With that minimum the gate resolves ticket, diff and comments
itself. Optionally:
- The caller's bundle (preferred): gaze's returned result block
  (`reviewed_head_sha`, intent, `plan check:`, unresolved lists), with
  `{pr, ticket}`.
- `integration`: run the declared integration checks whatever the diff
  touches (§ Check plan). A project asks for the same through its declaration.

Start the step clock before anything else (`skills/gaze/references/output.md` § Duration clock); its `end` line fills the verdict's `duration:`.

Every invocation produces the same verdict shape. Round is always derived from the
review's `verdict` entries in `refs/notes/review` (§ Gate sessions, § Notes review),
never from PR comments and never passed by the caller.

**Cwd prerequisite**: the gate uses `gh` and `git` commands that resolve
against cwd, and a `context: fork` invocation does **not** inherit the
caller's cwd. The caller passes `repo=<path>`, any checkout of the target
project that the caller keeps until the gate returns (its session or PR
worktree). The gate uses it only to locate the repository, never to read PR
state: whatever branch is checked out there is irrelevant.

**Isolation — the gate owns its checkout.** Every invocation, whoever the
caller, creates a fresh detached worktree on the PR head, rules from it and
removes it on exit. No caller hands the gate a tree, and the gate never reads
a tree another skill created: gaze removes its review worktree before it
returns, so a later gate run cannot rely on it.

Resolve the merge request with `python3 "$IDH_ROOT/scripts/forge.py" resolve <pr-number>`
(from `repo=<path>`). Its reads wait a short bound; an unreachable forge answers
from the mapping cached at an earlier contact with `"cached": true` and
`"forge": "unread (offline: ...)"` (ticket 1308): then skip the fetch below
and add the tree at its `head`. A refusal (never mapped) is ESCALATE, `Missing Data`.

```bash
PR_BRANCH=<head branch resolved from the forge for <pr-number>>
# <session-id>: the caller's session=, else the standalone UUID generated now;
# <round>: derived by `review_notes.py gate` (§ Notes review) before the tree exists.
primary_root=$(git -C "<repo-path>" rev-parse --show-toplevel) || exit 1
primary_root="${primary_root%%/.claude/worktrees/*}"
gate_tree="$primary_root/.claude/worktrees/gate-<pr-number>-<session-id>-r<round>"
git -C "$primary_root" fetch origin "$PR_BRANCH" || exit 1
if ! git -C "$primary_root" worktree add --detach "$gate_tree" origin/"$PR_BRANCH" || ! test -d "$gate_tree"; then
    echo "verify-gate: cannot create isolated gate worktree for PR <pr-number>" >&2
    exit 1   # verdict ESCALATE, root_cause_class: Missing Data
fi
```

On every exit path, after the verdict is recorded: `git -C "$primary_root"
worktree remove "$gate_tree"`. The session and round suffix keeps a
round-1 tree left behind by a refused removal from blocking round 2. The gate writes nothing in it, so a plain
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

## Check plan

Before running anything, the gate prints its plan: each check it will run,
reuse or skip, and why. The plan follows the paths the diff touches, as
classified once in `skills/merge/SKILL.md` § Gating tiers; the gate keeps no
path list of its own. On a gated base, from the gate worktree:

```bash
python3 "$IDH_ROOT/scripts/merge-gate.py" plan --base origin/<base-branch> --head HEAD \
    --since <prior head> [--integration]
```

`<prior head>` is the round-1 `ruled_tip_sha` on round 2, else
`reviewed_head_sha`. The plan prints one line per check declared in the
base's `.merge-gate.json`; adherence is one of them, the gate record's
`lint`. The gate runs no full test suite: only the declared before set runs
before the merge, the full set runs on main after it
(`skills/merge/SKILL.md` § Gating tiers).

- `reuse <check>`: the check passed in the latest published gate record for
  `<prior head>`, and the candidate is unchanged since that record's, head
  and base alike. The line names the source record, its head and candidate;
  copy it into the verdict verbatim. Any change re-runs the before set,
  which costs seconds.
- `run <check>`: no reusable result, with the reason (no record, failed
  there, the paths the delta touches). Run its command
  in the gate worktree. When every before-set check is `run` (none reused),
  write the record instead
  (`merge-gate.py run --base origin/<base-branch> --head HEAD`), which runs
  the same set, so a later round or the merge skill finds it.
- `skip <check>`: after-merge only (outside the declared before set), or an
  integration check (declared `"integration": true`) whose `"covers"` paths the diff does
  not touch. Integration tests are out of scope by default: they run when the
  diff touches what they cover, or when the caller passes `integration`.

Beside the plan, the gate runs the touched tests once, from the gate
worktree, gated base or not: `python3 "$IDH_ROOT/scripts/touched-tests.py"
--base origin/<base-branch>`. They are not a before-set check and leave no gate
record (the before set stays cheap); they catch before the merge what only the
integration tier sees, such as a moved symbol an integration test still
imports (ticket 1283). The verdict quotes the `selected:`, `fallback:` and
`result:` lines. Exit 1 fails the criterion the change carries (REROLL);
exit 4 (`skipped`, `incomplete`) is quoted as such, never as a pass.

A gate on an ungated base (the plan answers `off:`) applies the same rule by
hand: `merge-gate.py tier --since <prior head>` answering 0 reuses the check
results the prior verdict cites, re-running only the project's ticket check;
otherwise the project's declared gate runs (non-negotiable 2), integration
tests excluded unless covered or asked for.

## Review evidence

Seat reports are repository files under `tickets/reviews/<base>..<head>/`, one
per seat execution, written by the controller with
`review_evidence.py record`. The gate never reads a seat's verdict from prose.
Run the three steps sequentially: step 1 decides whether steps 2 and 3
apply, and step 2 needs its seats.

1. **Reports.** List the seats with a report on the branch: the file names
   under `tickets/reviews/` at the head, `<seat>-<n>.md`. With none, record
   `review_evidence: legacy` and judge the review comments as above; stop here.
2. **Seat table.** In the gate worktree, run
   `python3 "$IDH_ROOT/scripts/review_evidence.py" gate --repo "$gate_tree" --base origin/<base-branch> --ticket <ticket-file> --pr-body-file <body-file> --seat <seat>` (one `--seat` per reported seat; the body
   file is the merge request body, and the gate refuses a ticket it does not claim to close).
   Copy its `seat` lines into the verdict. A seat is `ran` (report on this head), `reused` (same patch-id,
   criteria hash and policy version, from an earlier head, which it names),
   `stale` or `no-report`. Check and gate results are reused or
   re-run as § Check plan says, never otherwise.
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
   Exit 4: the forge did not answer within the short read bound (ticket 1308):
   record `forge: unread (offline)` in `review_evidence` and the verdict text,
   never "no reviews", and rule on the rest; landing rechecks every human and
   Copilot review (`skills/merge/SKILL.md` step 3). A complete read prints
   `forge-read: <time>` first: pass it as the verdict's `--forge-read`.

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
duration: <text after "duration: " in the step_clock.py end line, e.g. 4m12s>
gate_session_id: <uuid>
review_worktree_path: <absolute path of the gate's own worktree>
ruled_tip_sha: <full commit SHA ruled>
pr: <pr-number>
ticket: <ticket-id>
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
    severity: must-fix | consider
    status: UNADDRESSED | WAIVED_WITHOUT_RATIONALE
unresolved_adherence_violations:   # failing adherence tests of the gate record's checks
  - test_id: <tests/test_x.py::test_y>
    check: <check name>
scope_overflow:
  - file: <path>
    reason: "<not traceable to exit criterion>"
    suggested_disposition: TICKETED | ESCALATE
checks:   # the § Check plan lines, each with its outcome
  - "run <check>: pass | fail(<exit>) - <reason>"
  - "reuse <check>: passed on record on <head> (candidate <oid>, <time>, <host>); <why>"
  - "skip <check>: <reason>"
review_evidence: legacy | {seats, forge}
  # seats: "seat <name>: ran|reused|stale|no-report (<verdict>) - <reason> <report>"
  # forge: "human: ran <login> ..." | "copilot: ran <login> ..." | "rejected <login> ... (<reason>)"
rationale: |
  <strongest remaining reviewer attack; if APPROVED, why evidence holds>
root_cause_class: Agent Error | Extractor Error | Original Error | Missing Data | Other  # required on REROLL/ESCALATE
reroll_bump: note verify-reroll — round {n}: {top unresolved criterion}  # only if REROLL — the gate writes nothing; the orchestrator poses this line
second_round_needed:   # only if REROLL
  - <prioritised items from unresolved lists>
```

## Decision rules

- Any `MISSING` in `per_exit_criterion` → REROLL (round 1) / ESCALATE (round 2).
- Any `UNRESOLVED` review comment from a human author → REROLL (round 1) / ESCALATE (round 2).
- Any `UNRESOLVED` gaze finding labelled severity ≥ medium →
  REROLL (round 1) / ESCALATE (round 2).
  Severity triggers apply to `blocking` findings. Tagged minors are triaged by tag, not severity.
- Any unresolved `verifiable:` minor (failing assertion still reproduces) → treated as
  blocker-adjacent: REROLL (round 1) / ESCALATE (round 2).
- A `blocking` finding or `verifiable:` minor without its `scenario:` and
  `on main:` fields (`skills/gaze/references/panel.md` § Finding tags) is
  read as a `consider:`.
- `consider:` minors are informational. They appear in the verdict comment but do not
  bounce the PR. Author is free to ignore.
- `nofollow:` minors are muted. The gate records them for the audit trail and does
  nothing else.
- Any `UNADDRESSED` must-fix simplify finding without rationale → REROLL (round 1) /
  ESCALATE (round 2).
- Any failing adherence check of the gate record → REROLL (round 1) / ESCALATE (round 2).
- Any `run` check that fails → REROLL (round 1) / ESCALATE (round 2). A check
  neither run nor reused nor skipped by the plan → ESCALATE.
- Any `stale` seat → REROLL (round 1) / ESCALATE (round 2).
- Any seat with `no-report` → ESCALATE. There is no merge with a recorded gap.
- A seat that ran or was reused with verdict `changes` keeps its findings
  load-bearing: they follow the review-comment rules above.
- Any `scope_overflow` entry with suggested disposition ESCALATE → ESCALATE.
- `scope_overflow` entries with all suggested dispositions TICKETED → does not block
  APPROVED. Caller handles ticket creation and PR annotation.
- When no rule above fires: an exit criterion or review finding that only the
  author can judge (scope, money, an irreversible step) → NEEDS-AUTHOR: the
  author decides whether to merge. It never overrides a REROLL or ESCALATE.
- All lists empty AND all criteria ADDRESSED → APPROVED.

**On REROLL**: write no ticket file — run no `erg log`, ever. Emit the bump line
in the verdict as a `reroll_bump:` field: `note verify-reroll — round {n}: {top unresolved criterion}`.
The gate runs in an isolated checkout over a shared `main`; a mid-wave `erg log`
on the ticket collides at the insertion point with the branch's own ticket
commits. The orchestrator poses the line: committed onto the PR branch with the
REROLL fix, or deferred to merge time.
For a verify-gate invocation outside raid, its caller owns posing
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

Tag definitions live in `skills/gaze/references/panel.md` § Finding tags (canonical source). Gate treatment:

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
- **Round derivation:** `review_notes.py gate` derives it (§ Notes review):
  the review's recorded verdicts, across every session and caller, plus one.
  PR comments are never counted. The caller never passes the round.
- **Two-round cap, every path.** Round > 2 → immediate ESCALATE, whoever calls
  and whether or not a session id was passed. A fresh session id does not reset
  the count. Past an ESCALATE the merge decision is the author's, not another
  gate run's.
- **What a re-gate reuses.** Round 2 plans with `--since` the round-1
  `ruled_tip_sha`: checks are reused or re-run as § Check plan
  says, seats as § Review evidence says. Exit criteria and review comments
  are always ruled afresh.
- **Caller enforcement.** The caller invokes the gate at most twice per
  session: round 1, then one re-gate after the fix. Raid never launches a
  third run and never opens a new session to escape the cap.
- **No gate without a completed review.** Standalone or from a caller, the gate
  is not run when the review's latest gaze answer on notes is ESCALATE, or when no
  gaze result was accepted for the current head (its `reviewed_head_sha` is
  stale). A moved head is not stale when what it adds since
  `reviewed_head_sha` is bookkeeping or nothing:
  `merge-gate.py tier --base origin/<base-branch> --head HEAD --since <reviewed_head_sha>`
  answers 0 (`skills/merge/SKILL.md` § Gating tiers). The only other
  documented caller path past a moved head is the round-2 re-gate of the fix
  for a round-1 REROLL (`skills/raid/SKILL.md` § Phase 6). Otherwise the gate
  answers ESCALATE without ruling the criteria, and the author decides.
  The gate reads the review's gaze answers on notes, the artifact raid polls,
  never a PR comment: a PR with no notes review (gazed before notes evidence)
  has no completed review, so gaze runs on it again. A refusal spends no gate
  round: the gate returns ESCALATE to its caller and posts, if anything, a
  comment headed `/verify-gate refused: no completed review`, never the
  `/verify-gate round=<n> verdict=<V>` pointer.

This admission is `review_notes.py gate`'s (§ Notes review), read from the
gaze `answer` entries.
Uses existing PR state for the criteria once that check passes.
Isolation is the same on every path (§ Isolation: own worktree, removed on exit).

## Output destinations

1. Structured verdict returned to the caller (raid, or the author), and its
   `verdict` entry on notes (§ Notes review), written before any comment.
2. The human-readable summary below is that entry's text (`--text-file`), the
   evidence. On a PR, then post one pointer line, best-effort:
   `/verify-gate round=<n> verdict=<V> ruled_tip_sha=<sha> · review on notes: <review_id>`.

   Take the `gate_session_id` from the caller's `session=` argument; with
   none (standalone), generate a fresh UUID. The review worktree path is the gate's
   own `$gate_tree`. Immediately before ruling, read the full tip SHA with
   `git -C "$gate_tree" rev-parse HEAD`; stop with ESCALATE if this fails.
   These are audit fields, written under the same snake_case keys as the
   structured verdict: callers (raid, merge, dashboard) read `ruled_tip_sha`.

   ```
   /verify-gate round=<n> verdict=<V>
   gate_session_id: <UUID from the caller's session=, or standalone UUID>
   review_worktree_path: <absolute path of the gate's own worktree>
   ruled_tip_sha: <full commit SHA read from that worktree>
   reroll_bump: <exact returned note verify-reroll line; include on REROLL, omit otherwise>
   Exit criteria: <addressed>/<total>  Review: <unresolved>  Simplify: <unresolved>
   Adherence: <blocking>  Scope overflow: <files> (<ticketed>/<escalate>)
   Checks: run:<n> reuse:<n> skip:<n> failed:<n>
   Minors: verifiable:<n> consider:<n> nofollow:<n> malformed:<n>
   Evidence: <legacy | ran:<n> reused:<n> stale:<n> no-report:<n>>
   duration: <the verdict's duration: value, e.g. 4m12s, or not measured>
   Top reasons (if not APPROVED): <ranked list>
   Rationale: <paragraph>
   ```

## Circuit breakers

- No ticket (no close claim, no title/body reference) → not a breaker. The
  PR body's stated intent and test plan stand in for exit criteria; record a
  `no_ticket` nit.
- A close claim naming a ticket file that does not exist → ESCALATE (dangling
  claim; the merge skill would fail on it). Resolve the claim in the gate worktree as
  `tickets/<id>-*.erg` **or** `tickets/closed/<id>-*.erg`, as the merge
  recipe does: callers close the ticket on the branch before gating, so a closed,
  archived ticket is the normal case and its exit criteria are read from
  `tickets/closed/`. Only neither path existing is dangling.
- PR body lacks test plan → not a gate-level failure, but recorded as a nit.
- Gate cannot access commit timestamps → ESCALATE (cannot distinguish pre/post comment changes).
- Contradictory signals between phases 2–5 → ESCALATE (no silent resolution).

## Notes review (`branch:<name>` and PR units)

A unit with a review in `refs/notes/review` (ticket 1274 for `branch:<name>
[base=<ref>]`, ticket 1300 for a PR number; design
`conception/2026-10-27-notes-review-spec.md` §5, §8) is gated as above with
round, admission, gaze findings and verdict taken from the notes, read and
written only through `python3 "$IDH_ROOT/scripts/review_notes.py" -C "$primary_root"`;
never `git notes` by hand.

- **Unit, branch.** `python3 "$IDH_ROOT/scripts/forge.py" resolve "branch:<name> [base=<ref>]"`
  (from `$primary_root`) gives `head`, `base`, `review_id` and `claims`, the
  branch's `Ticket:` trailers, which stand in for the close claim. No
  `review_id` → ESCALATE, `Missing Data`: no review request exists. The gate
  tree is `gate-<unit key>-<session-id>-r<round>`, the unit key as gaze names
  its tree (`branch-<name>`), added `--detach` at `head`; no fetch of a PR branch.
- **Unit, PR.** Branch, head, body and close claim come from the forge as
  above; the review is `review_notes.py find --unit pr:<n>`, keyed by the PR
  number, never by its branch name, which merge may reuse. Exit 1 with nothing
  on stderr: the PR has no notes review (gazed before notes evidence): no
  completed review, ESCALATE without ruling, spend no round; gaze runs again.
- **Unreadable remote.** Every lookup fetches the remote's reviews first. A
  failed fetch is a stale read, never "no review": with no local review the
  lookup refuses (`remote unreadable, no local review`, on stderr): ESCALATE
  naming it, `Missing Data`; with one, the gate rules on the local entries.
- **Round and review.** `review_notes.py gate <review_id> <head>` prints the state as
  JSON and exits 0 only when the gate may run. It reads the remote first when
  `origin` exists, so verdicts and answers of other clones count; a non-empty
  `stale` says that read failed and the round may be undercounted: write
  `notes: stale (<stale>)` in the verdict text. `round` is the
  recorded verdicts of the review, every session, plus one. It applies
  § Gate sessions' admission itself: an answer covers the head (its head
  equals the tip, or a rebased tip has the same non-empty verbatim patch-id),
  or the tip adds only bookkeeping to the latest reviewed head
  (`match: bookkeeping`), or it is the round-2
  re-gate of a round-1 REROLL fix descending from the rerolled head
  (`match: reroll-fix`). It refuses with no answer, an ESCALATE answer,
  a recorded ESCALATE verdict, or past two rounds. On a refusal answer
  ESCALATE with its `reason`, record nothing, spend no round.
- **Cross-family seat.** Before the `gate` call, read the change's row in
  `skills/route/references/decorrelation.md` § Scale the review to the risk
  from the diff. On the high-risk row, pass `--require-cross-family
  <producer family>` to `gate` and to `verdict`: the grid `family` of the
  writer line's model (the review's `writer` entries), never its runtime.
  `gate` then refuses an admitting answer whose `seat:` lines show no seat of
  another family that ran on a headless door, its family set by the launcher
  (`cross_family` lists those that count; a `self`, `subagent` or
  `unconfirmed` seat never does, and a REROLL-fix re-gate re-checks the
  answer the REROLL cited), whatever
  the plan's `no cross-family seat:` reason: ESCALATE `no cross-family seat`,
  spend no round; the caller parks the PR for a seat launched by the
  interface session (`skills/raid/references/detached-gaze.md` § No
  cross-family seat). Without a writer line, name the producer family from
  the caller's launch line; unknown, ESCALATE `Missing Data` (ticket 1326).
- **Review comments.** Non-negotiable 3's gaze findings are the `text` of
  every `answer` entry (`review_notes.py show <review_id>`) plus the open
  findings (`review_notes.py findings <review_id>`); attribution lines are in
  each answer's `attribution`. Commits after the answer's `ts` play the role
  of commits after a comment. On a PR, human and Copilot reviews and comments
  on the forge stay a read (§ Review evidence step 3) and bind as before.
- **Review evidence.** On `branch:`, step 2's body file is the branch's trailer lines,
  `git log --format='%(trailers:key=Ticket)' <base>..<head>`, and step 3 (forge reviews) records
  `forge: none`. On a PR both steps run as above.
- **Verdict.** Write the verdict text as one entry:
  `review_notes.py verdict --review <review_id> --session <uuid> --verdict <V>
  --head <ruled_tip_sha> --evidence <answer ids> [--candidate <gate record OID>]
  --text-file <file> [--forge-read <time>]`; `--forge-read` is step 3's
  `forge-read:` time, omitted (`unread`) when the forge went unread or on `branch:`. It prints `<entry id> local round=<n>`: the round it
  recorded, which is the verdict's `round`. The write is local, with a
  background sync nobody waits for; delivery is the landing push. It re-checks
  `gate`'s admission and refuses a head it does not admit, a third round and a
  REROLL on round 2 (rule ESCALATE instead). Exit 1 after writing: another gate
  run recorded the same round at once (stderr names it; ESCALATE to the
  author). On a PR, then post the one-line pointer (§ Output destinations) with
  that same round; a failed post changes nothing. On `branch:` nothing is posted.

## Not in scope

- **Merging.** The gate does not merge; that decision belongs to the caller.
- **Re-running what still holds.** The gate runs only its plan's `run` lines (§ Check plan). Review runs targeted tests only; the full declared set, integration checks included, runs once as the project's declared gate (here: after the merge, on main; `skills/merge/SKILL.md`, "Two moments").
- **Integration testing**, unless the diff touches what it covers or the caller or project asks (§ Check plan).
- **Acting on scope overflow.** The gate detects and reports; the caller tickets and annotates.
