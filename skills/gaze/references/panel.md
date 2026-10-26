# Gaze — review panel (Agent C)

Loaded from `skills/gaze/SKILL.md` § 2–5: the code panel, and the seat protocol the prose panel (`references/prose-panel.md`) shares.

### Review panel

Gaze runs the panel itself, from its own fork, on the review worktree
`$review_tree` created in phase 1; there is no separate review skill. The seats
launch with Agent A, as parallel background agents in one message, and are
collected by polling their artifacts (§ Fork execution contract). `<panel>` is
`$review_tree/.panel/<pr-number>/`, inside the worktree and never a temporary
directory: collection assumes launcher and seats share a filesystem.

1. **Manifest first.** Before launching, write `<panel>/manifest.txt`, one seat
   per line as `perspective<TAB>model<TAB>family<TAB>reason`, and run
   `python3 "$IDH_ROOT/scripts/panel-manifest-check.py" <panel>/manifest.txt --seats <panel_seats>`
   (drop `--seats` only under the default brief, `panel_seats: auto`);
   a line with an empty model, family or reason fails it, and so does a
   perspective the brief did not ask for or a brief seat the manifest lacks. Collection checks
   against this roster: without it, "no more reports are arriving" cannot be
   told from "none were ever launched".
2. **Launch.** Every code seat is the code-reviewer profile
   (`agents/code-reviewer.md`, contract `profiles/code-reviewer/PROFILE.md`).
   The perspective, the anchor HEAD, the changed-file roster, the ticket's exit
   criteria and the exact `<panel>/<perspective>.md` path ride in the launch
   prompt; the seat's rails (read-only, `git -C`, artifact protocol, report
   format) are the contract's and are not restated here.
3. **Artifacts.** Each seat writes `<panel>/<perspective>.md.part`, then renames
   it to `<panel>/<perspective>.md`. The rename is the completion signal.
4. **Collection.** One bounded polling loop, about ten minutes, until every
   manifest entry has its report or the deadline passes. Then classify each
   entry as reported or `no report`: a seat that only *returned* its findings
   reported to nobody. A `no report` seat gets the one retry of phase 6; never
   extend the deadline to hide a gap. A seat still missing after it is
   **missing, not clear**, recorded as § 2–4 Panel integrity says.

The code perspectives, from which the brief picks (brief names in
lower case, `red-team` and `doc-propagation` hyphenated):

| Perspective | Focus | Key question |
|---|---|---|
| **Correctness** | Logic, edge cases, test coverage | Does this do what the exit criteria say? |
| **Consistency** | Style, naming, docs, stale references | Does this fit the rest of the codebase? |
| **Scope** | Over-engineering, unrelated changes | Does this change *only* what the ticket asks? |
| **Red team** | Adversarial inputs, broken invariants | How can this break? |
| **Doc propagation** | Downstream text accuracy | Do docs and configs still match the code? |

**Fan-out preflight.** Check that the delegation tool is available before
launching. Spawn success is not a guarantee the agent exists: under a silent
child cap a spawn returned success for seats that never listed
(merge request #1143). When the runtime can list agents, poll that list; the
manifest and the landed artifacts are the source of truth for what ran. A
failed launch is handled as § 2–4 Panel integrity says. When the tool is absent because this fork is itself a
child, use the detached-seat substitution below; if nothing can launch, that
is a battery NOT-RUN (§ 2–4).

#### Detached-seat substitution

A child session does not inherit the runtime's agent connector. Substitute one
detached, headless, non-interactive CLI process per seat, launched from the
orchestrating session: a `claude -p "<prompt>"`
style invocation qualifies (measured working); a headless `vibe -p` session
cannot serve, its permission policy denies it file tools. Embed the whole seat
contract in the prompt: perspective, exit criteria, anchor HEAD, changed-file
roster, the `<panel>/<perspective>.md` path, and the read-only rails (writes
nothing outside its artifact, posts nothing, holds no credentials). Pin the cwd
to the review worktree, pass deny-rules as one quoted string, and request the
model pin; a CLI that cannot enforce it records that limitation in the report.
Launch each one through `python3 "$IDH_ROOT/scripts/seat_clock.py" run --cap 600
--out <panel>/<perspective>.md -- <cli...>`, which kills it at the cap and
records `no report (timed out after 600s)`.
Completion is observed by the polling above, never by the spawn's success. Cap
concurrent seats to the runtime's child cap and stagger launches; a seat beyond
budget or past the deadline is `no report`, never simulated.
`$IDH_ROOT/scripts/coaching/seat-runner.sh` is an optional heavier transport.

#### Synthesis and posting

1. **Preserve dissent** verbatim; the author decides.
2. **Triage by confidence**: investigate low-confidence findings before posting.
3. **Deduplicate** findings, never verdicts: a seat whose only finding merged
   into another's keeps its own verdict.
4. **Targeted tests only.** Gaze's seats, the adherence seat and `/verify-gate`
   run only the tests of the files the diff touches; none runs the full suite,
   which runs once, on the merge candidate, as the project's declared gate.
   Where the project declares `.idh-checks.json`, the targeted run is its scoped
   gate (`$IDH_ROOT/scripts/scoped-check.py`) and the review quotes its
   `selected:` and `skipped:` lines, never calling a scoped pass full.
5. **Write `<panel>/review.md` before posting**, so findings survive a forge
   outage or a failed post.
6. **Re-run the anchor first**, `python3 "$IDH_ROOT/scripts/review-anchor.py" <pr-number> --worktree "$review_tree"`: a nonzero `REVIEW-ANCHOR:` means the branch moved during review, so do not post.
   **Post a single review** on the merge request, each finding attributed to its
   seat, with what ran, by which family, and why.
7. **Verify it landed**: count the reviews before and after posting; if the
   count did not grow, the round did not happen. Say so and name
   `<panel>/review.md`.
8. **Verdict roster**, one line per manifest entry: `clear`, `concerns`,
   `blocking` or `no report`. A crashed seat and a clear seat are opposite
   outcomes and never share a spelling; `no report` is unresolved.
   `python3 "$IDH_ROOT/scripts/seat_clock.py" roster <panel>` gives each seat's
   wall time or failure (`timed out`, `failed to start`, `no report`); carry its
   lines into the result's `seat times:` line.

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
