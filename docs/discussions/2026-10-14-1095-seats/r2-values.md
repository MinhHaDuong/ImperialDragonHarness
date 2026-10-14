# R2, author's values seat (SIMULATED)

Every position below is SIMULATED. The real author arbitrates. The inputs were
r2-architect.md and probe-result.txt, which was run on git 2.43.0. The probe
confirms my round-1 finding 1: an excluded `.tmp/` is invisible to
`status --porcelain -uall`, it shows up only with `--ignored`, and a plain
`worktree remove` deletes it with exit 0. The fact is now measured, and it has
a positive control: `?? untracked.txt` was visible.

## Round-1 objections: status

| Objection (r1) | Status |
|---|---|
| The WIP rail cannot see `.tmp/`; it could silently delete evidence | **Answered.** There is no purge list and no pre-WIP deletion. WIP blocks removal of the whole tree, `.tmp/` included. An ordering-control test guards against anyone later adding `.tmp` to a pre-WIP purge |
| "Evidence is by definition not in `.tmp/`" | **Answered in substance.** `.tmp/` is declared disposable, and evidence goes where the project keeps it (commit, DVC or PR) |
| The purge must report what it removes | **Answered.** Roar and gc print `N files, X MB` before removal |
| The report must ship with A, not "later" | **Answered.** Option 2 contains Option 1 |
| "could not read N" instead of silent drop-out | **Answered**, with a mode-000 positive control |
| gc works on one repo; molt runs per project and per host | **Partly answered.** It is stated now, and doudou is covered "when molt runs there". Still a residual |
| An unmerged crashed tree keeps `.tmp/` indefinitely | **Accepted as residual and made visible.** That is acceptable |
| Option B reintroduces age-based deletion | **Answered.** B is dropped |
| Option C: a batched delete proposal for closed-ticket entries | **Withdrawn by me.** The architect is right that a `tNNNN-*` name does not prove ownership. Proposing deletion on a naming convention would be a claim the evidence cannot carry |

## What I still object to (SIMULATED)

1. **The roar check rests on self-attestation.** "Asks the agent to confirm
   nothing in it is cited by a verdict or PR" is a check whose all-clear an
   agent can give without looking. It should be mechanical and cheap: grep the
   PR body, the verdict files and the commit messages of the branch for
   `.tmp/`. Any hit blocks the removal until the cited file is moved. This is
   about 10 lines, and it turns the reading step into a gate.
2. **The restic exclude is not a "small item"; it belongs in the contract.**
   /home is 92% used and backed up nightly. Without the exclude, gigabytes of
   venvs and caches are copied into every snapshot before the worktree goes.
   That moves the cost to the backup repository and to restore time, quietly.
   It is a kindness cost that falls on the author, so put it in Option 2's
   definition of done and verify it with a planted file that is absent from a
   dry-run.
3. **The /home failure mode is worse when it happens, and molt runs rarely.**
   A report-only scan at molt cannot warn between runs. I do not ask for a
   daemon. I ask for one threshold line in the report, such as `/home above
   95%: WARN`, and for healthcheck to surface the same line at session start.
   That costs a few lines and needs no new mechanism.
4. **Measure doudou before claiming the outage is covered.** The documented
   outages are doudou project-test leaks. Option 2 helps padme's 74%, but
   neither option prevents the zoteus- or glossary-style leaks. The final
   record should say plainly: "harness names project leaks; projects fix
   them", and it should not count those leaks as solved.

## Assessment per option (SIMULATED)

- **Option 1 (observability only).**
  - Excellence: medium. It shortens diagnosis but leaves the cleanup itself
    with the author.
  - Integrity: high. It deletes nothing, its positive controls are named, and
    it shows both filesystems.
  - Kindness: cheap to build, but it costs author attention at every cleanup,
    which is the complaint that opened the ticket.
- **Option 2 (worktree `.tmp/` plus Option 1).**
  - Excellence: high. It answers WHERE and HOW at all three lifecycle points
    using existing mechanisms, and it is portable through plain git.
  - Integrity: high once objection 1 is fixed. It adds no new deletion path,
    and its fail-safe cases are tested: with no exclude, `.tmp/` counts as WIP
    and the tree is kept.
  - Kindness: good. It needs objections 2 and 3 fixed, so that the cost does
    not move silently to backups and /home.

## Ranking (SIMULATED)

1. **Option 2, landed as two PRs: Option 1 first.** That PR also runs Option
   1 on doudou, which is the cheap measurement. Then the `.tmp/` contract. This
   order lets the report observe the before-and-after effect of the rule,
   which gives the rule its own positive control.
2. **Option 1 alone.** It is the honest fallback if the author prefers not to
   change agent habits yet.

| Option | One change that would most raise it |
|---|---|
| 1 | A `/home` and `/tmp` threshold WARN line, also surfaced by healthcheck at session start |
| 2 | Replace roar's agent confirmation with a mechanical grep for `.tmp/` citations in the PR, verdicts and commits that blocks removal; make the restic exclude part of the definition of done |
