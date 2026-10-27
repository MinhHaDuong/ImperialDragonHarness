# Gaze — seat protocol

Loaded from `skills/gaze/SKILL.md` § 3: how gaze launches and collects the
items of its plan. The prose seats (`references/prose-panel.md`) share it.

### Launch and collection

Gaze runs the plan itself, from its own fork, on the review worktree
`$review_tree` created in phase 1. `<panel>` is `$review_tree/.panel/<pr-number>/`,
inside the worktree and never a temporary directory: collection assumes
launcher and seats share a filesystem. The plan file `<panel>/manifest.txt`
(`references/plan.md`) is written before anything launches.

1. **Launch.** Every code seat is the code-reviewer profile
   (`agents/code-reviewer.md`, contract `profiles/code-reviewer/PROFILE.md`).
   The intent, the perspective, the anchor HEAD, the changed-file roster
   inside the what, the ticket's exit criteria and the exact
   `<panel>/<name>.md` path ride in the launch prompt; the seat's rails
   (read-only, `git -C`, artifact protocol, report format, its first line
   naming its model and family) are the contract's and are not restated here.
   Every seat prompt also carries the reach rails: the tree is read only as
   `git -C "$primary_root/.claude/worktrees/review-<pr-number>" ...`; no
   working-tree overwrite (`git checkout <ref> -- `, `git restore .`,
   `git reset --hard`), another version is read with `git show <ref>:<path>`;
   an unreachable tree, or a HEAD other than the anchor, is a NOT-RUN refusal,
   and the seat never falls back to the session cwd.
   Launch every seat of the plan in one message, as parallel background agents.
   A check item runs as a script through
   `python3 "$IDH_ROOT/scripts/seat_clock.py" run --cap <s> --out <panel>/<name>.md -- <command>`.
2. **Artifacts.** Each seat writes `<panel>/<name>.md.part`, then renames it to
   `<panel>/<name>.md`. The rename is the completion signal.
3. **Collection.** One bounded polling loop, within the plan's budget and
   never past gaze's 15-minute deadline, until every plan item has its report
   or the deadline passes. At the deadline, stop the seats the runtime can
   stop; a late report is not read. A seat that only
   *returned* its findings reported to nobody. There is no retry: a seat with
   no report at the deadline is missing, not clear, and the plan check names
   it. Never extend the deadline to hide a gap.

**Fan-out preflight.** Check that the delegation tool is available before
launching. Spawn success is not a guarantee the agent exists: under a silent
child cap a spawn returned success for seats that never listed (merge request
#1143). The manifest and the landed artifacts are the source of truth for
what ran. When the tool is absent because this fork is itself a child, use the
detached-seat substitution below; a seat nothing could launch has no report.

#### Detached-seat substitution

A child session does not inherit the runtime's agent connector. Substitute one
detached, headless, non-interactive CLI process per seat, launched from the
orchestrating session: a `claude -p "<prompt>"`
style invocation qualifies (measured working); a headless `vibe -p` session
cannot serve, its permission policy denies it file tools. Embed the whole seat
contract in the prompt: intent, perspective, exit criteria, anchor HEAD,
changed-file roster, the `<panel>/<name>.md` path, the first-line rule, and the
read-only rails (writes nothing outside its artifact, posts nothing, holds no
credentials). Pin the cwd to the review worktree, pass deny-rules as one
quoted string, and request the model pin; a CLI that cannot enforce it records
that limitation in the report. Launch each one through
`python3 "$IDH_ROOT/scripts/seat_clock.py" run --cap 600 --out <panel>/<name>.md -- <cli...>`,
which kills it at the cap and records `no report (timed out after 600s)`.
Completion is observed by the polling above, never by the spawn's success. Cap
concurrent seats to the runtime's child cap and stagger launches; a seat beyond
budget or past the deadline is `no report`, never simulated. The same door
serves an other-family seat (`skills/route/references/decorrelation.md`).
`$IDH_ROOT/scripts/coaching/seat-runner.sh` is an optional heavier transport.
An external reviewer routed by `skills/reviewers/SKILL.md` is a plan item
like any other; its route's `SEAT-FAILED:`, `SEAT-MISSING:` and
`PANEL-INTEGRITY:` records go verbatim into the plan check's deviations: an
unavailable route is never reported as a clean review.

#### Synthesis and posting

1. **Preserve dissent** verbatim; the author decides.
2. **Triage by confidence**: investigate low-confidence findings before posting.
3. **Deduplicate** findings, never verdicts: a seat whose only finding merged
   into another's keeps its own verdict.
4. **Targeted tests only.** Gaze's checks and seats run only the tests of the
   files the what touches; none runs the full suite, which runs once, on the
   merge candidate, as the project's declared gate. Where the project declares
   `.idh-checks.json`, the targeted run is its scoped gate
   (`$IDH_ROOT/scripts/scoped-check.py`) and the review quotes its
   `selected:` and `skipped:` lines, never calling a scoped pass full.
5. **Write `<panel>/review.md` before posting**, so findings survive a forge
   outage or a failed post.
6. **Re-run the anchor first**, `python3 "$IDH_ROOT/scripts/review-anchor.py" <pr-number> --worktree "$review_tree"`: a nonzero `REVIEW-ANCHOR:` means the branch moved during review, so do not post.

#### Finding tags

Every non-blocking finding carries exactly one prefix; `blocking` findings are
not tagged. `/verify-gate` reads the same set.

| Prefix | Meaning |
|---|---|
| `verifiable:` | Evidence attached now: a failing test_id, command output or SHA:file:line (code); a line citation or numeric recheck (prose). |
| `consider:` | A hypothesis, not enforced; the author may dismiss it. |
| `nofollow:` | Deliberately not pursued (out of scope, duplicate, taste); recorded only. |

"This might break X" without evidence is either made `verifiable:` or
downgraded to `consider:`; a `verifiable:` finding without its evidence is held
until it has some.

| Severity | Seat verdict |
|---|---|
| Breaks correctness (bug, data loss), or a defect this PR introduces | `blocking` |
| Pre-existing but touched | `concerns`; a ticket only above the `rules/workflow.md` severity floor |
| Pre-existing and untouched | investigate; ticket if warranted |
