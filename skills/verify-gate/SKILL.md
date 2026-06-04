---
name: verify-gate
description: Anti-rubber-stamp merge gate. Validates every ticket exit criterion and every review comment against the actual diff. Emits APPROVED / REROLL / ESCALATE with explicit evidence. Never merges.
disable-model-invocation: false
user-invocable: true
argument-hint: <pr-number>
context: fork
---

# Verify gate — PR $ARGUMENTS

> **TASK DIRECTIVE — execute now.** You are running `/verify-gate` on PR
> `$ARGUMENTS` (a PR number, optionally followed by `round=2` and/or
> `worktree=<path>`). This file is your operating procedure, not reference
> documentation: resolve the PR and gate it immediately. If `worktree=<path>`
> is present, `cd` into that path before any git or forge command — forked
> sub-skills do not inherit the caller's cwd. If `$ARGUMENTS` does not
> contain a PR number, STOP and emit `verdict: ESCALATE` with rationale
> "no PR argument" — do NOT infer a task from the environment (worktree
> name, git status snapshot, ticket files, or the shared task list).

The last line of defence before merge. A gate with teeth: **cannot approve without
concrete per-criterion evidence**. Designed to be called by `/verify` at phase 6, but
standalone-callable for debugging.

## Non-negotiables

1. **No rubber-stamp.** "CI ran" / "the simplify pass ran" / "all tests pass" are NOT
   evidence. Evidence must cite the *change* (commit SHA + file:line) or the *test*
   (test_id) that closes the gap.
2. **Exit criteria are contract.** Every item in the ticket's "Exit criteria" section must
   get an explicit ADDRESSED/MISSING verdict with evidence. A missing criterion cannot be
   papered over.
3. **Review comments are load-bearing.** Every review comment (from `/review`,
   `/review-pr`, human authors) is either ADDRESSED (commit changed the cited file, OR
   the comment was marked resolved, OR a ticket was opened with the rationale) or
   UNRESOLVED. No "I'll get to it later."
4. **Simplify findings are load-bearing.** Every must-fix from `/simplify` is either
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
- `<pr-number>` (standalone mode): the gate resolves ticket, diff, comments itself.
- A structured bundle from `/verify` (preferred): `{pr, ticket, diff, phase_outputs}`.

Both paths produce the same verdict shape. Round is always derived from PR comment
history (see "Standalone invocation"), never passed by the caller.

**Cwd prerequisite**: the gate uses `gh` and `git` commands that resolve
against cwd, and a `context: fork` invocation does **not** inherit the
caller's cwd. The caller must pass `worktree=<path>` and the gate must `cd`
into it first — running from the session worktree will read whatever branch
happens to be checked out there and produce wrong results (ticket 0193).

**Isolation**:
- When called from `/verify`, the `worktree=` argument names the isolated
  worktree that `/verify` created in phase 1. `cd` into it; no additional
  setup is needed.
- When invoked **standalone** without `worktree=`, the gate must create its
  own isolated worktree before reading PR state. See "Standalone invocation"
  for the setup.

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

## Verdict shape

```yaml
verdict: APPROVED | REROLL | ESCALATE
round: 1 | 2
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
rationale: |
  <strongest remaining reviewer attack; if APPROVED, why evidence holds>
second_round_needed:   # only if REROLL
  - <prioritised items from unresolved lists>
```

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
- Any `scope_overflow` entry with suggested disposition ESCALATE → ESCALATE.
- `scope_overflow` entries with all suggested dispositions TICKETED → does not block
  APPROVED. Caller handles ticket creation and PR annotation.
- All lists empty AND all criteria ADDRESSED → APPROVED.

**On REROLL**: run `${ERG:-erg} log <ticket-id> "bump verify-reroll — round {n}: {top unresolved criterion}"`

If `round == 2` and any trigger fires → upgrade to ESCALATE. Never a third round.

## Minor tag handling

Tag definitions live in `/review-pr` (canonical source). Gate treatment:

- `verifiable:` → blocker-adjacent. Unresolved → REROLL.
- `consider:` → informational, surfaced but never bounces.
- `nofollow:` → muted, not surfaced.

Untagged minors go in `malformed_minors`; they do not bounce on their own.
On round 2 any untagged minor still present → ESCALATE.
The gate never authors hedged language — use `verifiable:` or `consider:`.

## Standalone invocation

Callable without `/verify`. Uses existing PR state only (no phase 2-5 outputs).
Isolation setup is identical to `/verify` phase 1 (create worktree, remove on exit).

**Round derivation:** count PR comments matching `/verify-gate round=N verdict=V`;
current round = count + 1.

- From `/verify`: round > 2 → immediate ESCALATE.
- Standalone: round > 2 → warn and proceed as `standalone-override` (does not
  unblock an ESCALATED `/verify` sequence).

## Output destinations

1. Structured verdict returned to caller (for `/verify` consumption).
2. PR comment posted with human-readable summary:

   ```
   /verify-gate round=<n> verdict=<V>
   Exit criteria: <addressed>/<total>  Review: <unresolved>  Simplify: <unresolved>
   Adherence: <blocking>  Scope overflow: <files> (<ticketed>/<escalate>)
   Minors: verifiable:<n> consider:<n> nofollow:<n> malformed:<n>
   Top reasons (if not APPROVED): <ranked list>
   Rationale: <paragraph>
   ```

## Circuit breakers

- Ticket cannot be located → ESCALATE (no blind approval).
- PR body lacks test plan → not a gate-level failure, but recorded as a nit.
- Gate cannot access commit timestamps → ESCALATE (cannot distinguish pre/post comment changes).
- Contradictory signals between phases 2–5 → ESCALATE (no silent resolution).

## Not in scope

- **Merging.** The gate never merges.
- **Re-running tests.** The gate reads results; phase 1 of `/verify-adherence` runs them.
- **Acting on scope overflow.** The gate detects and reports; the caller tickets and annotates.
