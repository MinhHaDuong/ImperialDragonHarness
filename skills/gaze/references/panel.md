# Gaze — seat protocol

Loaded from `skills/gaze/SKILL.md` § 3: how gaze launches and collects the
items of its plan. The prose seats (`references/prose-panel.md`) share it.

### Launch and collection

Gaze runs the plan itself, from its own fork, on the review worktree
`$review_tree` created in phase 1. `<panel>` is `$review_tree/.panel/<pr-number>/`,
inside the worktree and never a temporary directory: collection assumes
launcher and seats share a filesystem. The plan file `<panel>/manifest.txt`
(`references/plan.md`) is written before anything launches.

1. **Launch.** The default door is a detached headless CLI, one per seat,
   which does not nest inside gaze's own agent tree and so launches at any
   depth on Claude Code, Codex and Pi alike. Write the brief once to
   `<panel>/brief.md` (the intent, the ticket's exit criteria, the
   changed-file roster inside the what), then launch each seat as a
   background shell command:

   ```bash
   python3 "$IDH_ROOT/scripts/gaze_seat.py" launch --runtime <door> \
     --model <pin> --family <family> --home-family <gaze's own family> \
     --perspective <perspective> --panel <panel> --name <item> \
     --review-tree "$review_tree" --anchor <head> --base <base-ref> \
     --brief <panel>/brief.md [--role code-reviewer|prose-reviewer]
   ```

   The door, model and family come from the plan item; the runtime's door
   (`launch_doors.<door>.headless` in `skills/route/routes.json`) supplies the
   command template and its `seat_rails`: read tools only, with no shell and
   no write tool, where the CLI takes an allowlist; a sandboxed door holds the
   seat read-only by its sandbox. A seat without a shell runs no tests and no
   git: a behaviour claim is a check item, and the script writes the diff
   `<base>...HEAD` to `<panel>/<name>.diff` for the seat to read. The script
   builds the prompt from the role's profile Charter (`--role`:
   `code-reviewer` by default, `prose-reviewer` for a prose seat) plus the
   launch parts (perspective, anchor, diff path, reach rails below), pins the cwd to the review tree, runs the seat
   under `seat_clock.py`'s cap
   (600 s by default; set `--cap` within the plan's budget) and files
   `<panel>/<name>.md` with its first line `worker: model=<pin> ·
   family=<family>` set from the pin, never from the CLI's self-report.
   Anything that stops a seat, its own `NOT-RUN:` refusal included, is
   `<name>: no report (<reason>)` in
   `<panel>/<name>.md.status` and no report at all: the plan check counts the
   seat missing, and gaze never replaces it with its own read.
   `--dry-run` prints the command and launches nothing.

   **Subagent door.** Where the runtime's delegation tool is present, a seat
   of gaze's own family may instead be the code-reviewer profile
   (`agents/code-reviewer.md`, contract `profiles/code-reviewer/PROFILE.md`),
   launched as a background agent with the intent, the perspective, the
   anchor HEAD, the roster, the exit criteria and the exact
   `<panel>/<name>.md` path in its prompt; the seat's own rails are the
   contract's. Launch every such seat in one message, as parallel background
   agents, and wait by polling for their artifacts (step 3).

   Either door, the seat carries the reach rails: the tree is read only as
   `git -C "$primary_root/.claude/worktrees/review-<pr-number>" ...`; no
   working-tree overwrite (`git checkout <ref> -- `, `git restore .`,
   `git reset --hard`), another version is read with `git show <ref>:<path>`;
   an unreachable tree, or a HEAD other than the anchor, is a NOT-RUN refusal,
   and the seat never falls back to the session cwd.
   A check item runs as a script through
   `python3 "$IDH_ROOT/scripts/seat_clock.py" run --cap <s> --out <panel>/<name>.md -- <command>`.
2. **Artifacts.** Each report lands as `<panel>/<name>.md.part`, then is
   renamed to `<panel>/<name>.md` (by `gaze_seat.py` on the headless door, by
   the seat on the subagent door). The rename is the completion signal.
3. **Collection.** One bounded polling loop, within the plan's budget and
   never past gaze's 15-minute deadline, until every plan item has its report
   or the deadline passes. At the deadline, stop the seats the runtime can
   stop; a late report is not read. A seat that only
   *returned* its findings reported to nobody. There is no retry: a seat with
   no report at the deadline is missing, not clear, and the plan check names
   it. Never extend the deadline to hide a gap.

**Fan-out preflight.** On the subagent door, spawn success is not a guarantee
the agent exists: under a silent child cap a spawn returned success for seats
that never listed (merge request #1143). On either door the manifest and the
landed artifacts are the source of truth for what ran, and completion is
observed by polling, never by a spawn's or a process's start. Cap concurrent
headless seats to what the host and the providers' rate limits bear, and
stagger launches.

#### Doors that cannot serve

A door whose CLI cannot hold a seat read-only has no `seat_rails` in
`routes.json`, and `gaze_seat.py` refuses it: a headless `vibe -p` session
cannot serve, its permission policy denies it file tools. A rail or a model
pin a CLI cannot enforce is recorded in the report as that limitation.
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
not tagged. Verify-gate reads the same set.

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
