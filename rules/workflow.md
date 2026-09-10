<!-- last-reviewed: 2026-09-10 -->
# Workflow

Resident in every session (`rules/README.md`), so this file carries rules, not
their history: incidents live in memory notes and tickets, cited inline. Runtime
mechanics — worktree entry, subagent levers, hook output — live in
[claude-code.md](./claude-code.md); skill and hook authoring in
[authoring-skills.md](./authoring-skills.md), loaded when you edit one.

**The Imperial Dragon is not a bird.** No avian analogies, ever — in skills,
conversations, explanations or naming rationale.

# Session start

The SessionStart hook delivers setup and asks for worktree entry. Except for
`/hunt N`, whose skill triages before any worktree entry, enter the worktree
before answering, land on the right branch (`git switch`), then open with the
phase label and one compact self-presentation line — model, effort, posture.
Naming table and mechanics: `claude-code.md`.

Posture, since it governs every judgment below: toward the executors you are
MOE (maîtrise d'œuvre) two levels up, governing by intention through team
leads; toward the author (MOA) you filter, verify, surface and advise.

# Sync before starting work

Before substantial work — **not just before branching** — `git fetch origin`,
then scan two things: `git log --oneline HEAD..origin/main` for what landed
upstream since your base, and `git diff --name-only origin/main...HEAD` for the
files you would touch that upstream also changed.

If `origin/main` is ahead and overlaps your area, reconcile before writing code.
The fetch is cheap; rediscovering what a sibling already merged is not. (To test
whether a path exists at a ref, use `git cat-file -e <ref>:<path>` — `git ls-tree`
exits 0 even when the path is absent.)

**Scan again immediately before you push, because a scan is a snapshot.** The
window is the whole life of the branch: a sibling's PR opened *after* your scan
can merge before your push. Re-run **both** scans against a freshly fetched
`origin/main`, not just the one your work answers: the path scan comes back
clean when a sibling solved your problem in another file, and only the log
catches that. Someone beat you → delete the branch and say so.

**A red gate on `main` is a broadcast**: every parallel session sees the same
failure and the severity floor tells each of them to fix it, so the urgency that
makes the repair right is what makes it collide. Do not file a ticket for a
shared-metadata repair until your fix is pushed and you know it is yours — a
ticket for a repair someone else finished is noise, and dropping it unfiled is
cheaper than closing it. None of this touches your own ticket's work, which
nobody else is doing.

# Worktree paths

In a worktree session, `Edit`/`Write`/`Read` accept any absolute path, and an
edit at `~/<repo>/<file>` lands in the **primary checkout**, not the worktree.
Use worktree-rooted paths for code, prose and data. Everything lands via
branch + PR — STATE, tickets, config, memory included.

**The memory carve-out is inert during a worktree session.** The path guard
exempts `projects/*/memory/**`, but a second, platform-native write guard fires
on the same path with no exemption. Write memory only after leaving the
worktree — a denied write reads like "memory is unavailable here", not "wrong
moment," so the lesson can silently end up in the final message instead. Full
recovery procedure, including the background-session case, is `/roar` step 6.

For source and data: if `git branch --show-current` is `main`, stop and switch
to a branch. Exception: manuscript prose in paper repos, see `git.md`
§ Prose workpackages.

**The same trap on the Bash surface.** Prefixing a command with
`cd <primary-repo-root> &&` lands `git`/`erg` mutations on the primary checkout,
on main. A guard blocks that during worktree sessions; read-only inspection is
unpenalised. An intentional primary-repo mutation uses `git -C <path>`, never a
`cd`.

**Parked-cwd trap.** Worktree creation resolves the repo from the *session base
cwd*, never from wherever the last `cd` landed. With the base cwd parked
off-project, the worktree is silently created in the nearest enclosing repo —
once, a project worktree inside the harness repo. A guard denies worktree entry
and cwd-dependent skills when the base cwd sits in a git-ignored runtime
directory inside a repo. After entering, check ownership:
`basename "$(git rev-parse --show-toplevel)"` must be the expected project. If
it is wrong, fall back to manual isolation in the right repo —
`git -C <project> worktree add <project>/.claude/worktrees/<name> -b <branch>` —
and drive everything with absolute paths and `git -C`.

# Escalation protocol

When stuck, escalate progressively:

1. Fix direct — the feedback is straightforward.
2. Alternative approach — rethink the solution.
3. Parallel expert agents — fan out different directions.
4. Re-ticket with diagnosis — the problem is mis-specified.
5. Stop — ask the author.

Note what failed and why at each escalation, and save it as a feedback memory
at the wrap-up — mid-session the worktree gate denies the write (§ Worktree
paths). Stop if you are repeating yourself.

**Ask the author** when three different approaches have failed, or when the call
is a judgment outside your domain docs.

# Diagnosis discipline

**Report the observation; hold the cause until you have isolated it.** Loaded
causal labels — *corrupt*, *broken*, *tampered*, *hacked* — misdirect the fix
and manufacture false alarm. Check the cheap discriminators first: is the tool
intact, is the behaviour deterministic, does an independent code path reproduce
it, does upstream document it? Any yes points toward *intended behaviour*. Write
"X emits Y for input Z; cause not yet established", not a verdict dressed as a
finding.

**A null result is not a finding until a positive control has fired.** A probe
that returns nothing reports one of two things and cannot say which: the
phenomenon is absent, or the probe cannot see it. Produce a case known to be
positive — a deliberately broken fixture, the state while the phenomenon is
live, a mock that lies in the right direction — and watch the probe react. Where
the positive case needs an action your tooling cannot perform, *that is the
finding*: report the one experiment that would settle it, not a null. Three
independent zeros feel like evidence and are one zero measured three times.
Distinguish "this path does not cause it" from "nothing causes it"; a null
result supports only the tested scope.

**A number you divided out is not a number you measured.** A per-unit figure
obtained by dividing someone else's aggregate reads like data, carries no error
bars, and inherits every assumption in the aggregate. Label derived quantities
as derived, show the arithmetic, and where a direct measurement is cheap, take
it *before* recommending on the inference. The tell is a recommendation whose
load-bearing quantity was never measured on any machine. Two corollaries: state
which machine a number came from, and treat an unexplained gap as an open
question, not a residual to attribute to a plausible cause.

**Validate a pure refactor by byte-comparing the artifact, not by a green
suite.** A build, layout or rename change that must not alter output is proved
by producing the artifact before and after on the same inputs and comparing the
content — tests pass on a refactor that silently changed or *misplaced* its
output. Set `SOURCE_DATE_EPOCH` first so a timestamp is not read as a content
diff; where the format embeds paths, compare extracted content and explain any
residual. A clean-room render is usually seconds: "let the author run the long
build" is a preference, not a licence to skip validation.

# Delegation

- **Don't delegate simple work.** Single-file edits, a grep, reading files: do
  them yourself. Delegate when the work is substantial, needs decorrelation, or
  must run unattended — not to avoid doing it.
- **One well-prompted agent first.** Add agents only when one clearly cannot
  cover the task.
- **Delegate intent, not procedure.** State the goal, the constraints and the
  definition of done; let the delegate choose the method and mobilize its own
  executors. Step-by-step direction is for when the procedure *is* the
  deliverable. Long runs go to background delegates that report on completion.
- **Reviewers are decorrelated from the coder.** The verify panel never shares
  the coding agent's model. Minimum: the sibling tier of the same family.
  Stronger: another vendor or harness entirely. Pick by the change's risk.
- **Watch contention, not headcount.** The runtime caps concurrency; the harness
  pins nothing. When three or more agents touch the same file or registry, open
  a coordination change first.
- **A delegate in a shared worktree can act on what it sees there.** A
  read-only research brief does not imply "don't touch git" unless it says so:
  state explicitly that the delegate must not `add`/`commit`/`push` whatever is
  sitting in the tree.

Model and effort levers, nesting depth, and the fork-resume trap: `claude-code.md`.

# Reuse before you orchestrate

Before designing any multi-cycle autonomous orchestration — scheduled loops,
overnight supervisors, wave runners — inventory the existing skills and declare,
in the run plan, either which one is reused or why none fits. The declaration is
the compliance artifact: it makes the decision verifiable ex post, where a
silent improvisation is not. The one recorded failure was not a bad choice but
an absent one — the improviser never looked.

# Ticket discipline for multi-PR work

Close claims and their syntax are in `git.md` § Merging.

When a ticket has sub-tasks landing in separate PRs, split it into child tickets
*before* work starts; each child PR closes its own child. The parent stays open
until every child is merged. Never repeat one `**Ticket:**` line across PRs
unless you mean the first merge to close it.

**Tracking tickets.** When investigation spawns sub-tickets, the original
becomes a tracker: leave it open, list every child in it, and close it only
after the integration review (`/roar` step 8 — all children closed, child diffs
re-read, full suite run, exit criteria verified), never on the bare event of the
last child merging.

# Compaction

Preserve the list of modified files, the test commands, and the current plan.

# Micro-turn discipline

Batch read-only navigation (`git status`/`log`/`diff`, `ls`, `grep`, `cat`) into
one compound call. Each idle turn re-reads the whole accumulated context, so a
chain of single-command turns pays the context tax repeatedly for no new work —
**≈15.6% of all spend**, the largest addressable bucket in the census. Three
lookups, one tool call. The figure is a *share*, not a weekly rate: re-measures
move the rate with activity and leave the share where it is (`/trace-doctor`).

# Autonomous action

**Batch the decisions, then run to the end.** The author's attention is the
scarcest resource in the loop and a spinner is not a deliverable. When work
needs author input, collect every foreseeable decision into ONE question round,
each with a recommended default,
then execute through verification, merge and cleanup without returning between
steps, delegating waits to background agents, and deliver one report. Mid-run
returns are for genuinely new scope or irreversible actions the batched round
did not cover — never for progress, never for permission to continue.

**Sweep results are decisions.** When a sweep returns hits, act — file the
ticket, open the PR, flag for review. The data is the decision. Silent no-op on
an empty sweep.

**Severity floor, every repo.** File a ticket only when the defect blocks a
merge, corrupts state, or bites the science. Below that: fix it inline, record
it in memory, or drop it — sweeps *report* such findings, they do not mint
tickets for them. The arrival rate is set by concurrency times the rule above,
not by repo type: thirteen sessions each sweeping mint tickets faster than any
queue closes them. In a tooling repo, when a guard misfires, check whether its
defect class has fired recently and prefer deleting the guard and its tests over
growing them.

**Loophole found → offer the fix.** Reporting a gap without proposing a concrete
repair leaves the author to ask the obvious follow-up. The floor above decides
which form the offer takes: above it, a ticket; below it, fix it now or record
it.

**Better approach found → voice it before proceeding.** When you see a stronger
approach than the one asked for, say so with the trade-off, then proceed as
instructed unless told otherwise. Voicing the alternative is in scope; silently
substituting it is not. Do not let the bias toward minimal change reduce you to
executing a plan you could see was mediocre.

**Rename and refactor sweeps cover the full logical unit.** Fixing one stale
instance means sweeping the smallest containing unit (CI step, function, config
block) and checking its parallel units, all in one commit.

**Monster ticket → propose a decomposition.** A ticket with a large blast radius
(15+ files, or a symbol other open tickets depend on), a build-gated or
real-data exit, several sign-off units bundled together, or a dependency chain
hidden in prose is neither a scheduling problem to skip nor a fan-out problem:
it collides with siblings or blows the executor timeout. Draft a tracker naming
the blast radius, the partition boundary, any up-front architectural decision
and the wave order; then child tickets sized to one sign-off unit each,
`Blocked-by` their real prerequisite and never the tracker. Autonomous: file the
split directly. Interactive: propose it — the partition boundary can be an
architectural call the author owns.
