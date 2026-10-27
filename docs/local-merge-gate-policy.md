# Local merge gate: policy and adoption guide

Status as of 2026-10-21. Written at the author's request so the policy can be
adopted in other projects. Decided in tracker 1045. Today only the forge
settings are in place (the light ruleset, no required checks, GitHub Actions
disabled), together with the gate-record machinery, the guard hook and the daily audit.
The gate itself is on: `.merge-gate.json` declares `"gate": "on"` (ticket 1156).
Each part still open is marked **pending** with its ticket.

## Principle

The merge gate is local; the forge is a host, not an authority. Trust is a base
principle, so the gate leaves no open door: it adds traceability. Two things must
be answerable after the fact: what was run (when, by whom, on which host and
revision), and whether anyone got around the gate. A record is a statement that
can be traced, not proof. Nothing depends on one agent runtime: the basis is git
and the forge, which hold for any agent and for a human.

## The flow

The expensive check runs once, last, on the merge candidate, or, for a
bookkeeping merge on an open fast path, on the new main tip right after the
merge. Earlier stages run only what they need.

| Stage | Where | What runs |
|---|---|---|
| 1. Work | the author's or agent's machine | scoped tests of the touched files |
| 2. Rebase onto the base branch, resolve conflicts | local git | nothing |
| 3. Review (code review and the merge-gate review) | local seats | read the diff; targeted tests of the touched files only |
| 4. Changes needed? | | back to stage 1; no full run yet |
| 5. Candidate | the harness | merge the pull request into the base locally, run the full check set once on that commit (the fast-path checks only, for a bookkeeping diff on an open fast path), write the gate record |
| 6. Merge | the merge helper | refuses without a passing record on that candidate |

A failed candidate sends the pull request back to stage 1; it then passes through
stages 2, 3 and 5 again. That is the only case where the full set runs twice
on one change.
A bookkeeping diff (tickets, STATE.md, memory) gets a lighter record, the
checks `.merge-gate.json` lists for its tier, so the trace stays uniform and
the cost stays small. A
bookkeeping diff on an open fast path (ticket 1226) runs only the fast-path
checks; the full set then runs on the new main tip, after the merge, through
`scripts/merge_monitor.py`. The policy is `skills/merge/SKILL.md` § Gating tiers. In place
(tickets 1171 and 1156 closed; the fast path, ticket 1226). Ticket 1172, reading the forge's result for a head, was closed as superseded by this flow.

## Forge settings

- **No required status checks.** The forge's required-checks ruleset is disabled.
- **No pull-request requirement.** It was judged friction for the author.
- **A light ruleset** on the default branch: restrict deletions and block force
  pushes, with an empty bypass list. Create it with the repository rules API:

  ```json
  {"name":"main-traceability","target":"branch","enforcement":"active",
   "bypass_actors":[],
   "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
   "rules":[{"type":"deletion"},{"type":"non_fast_forward"}]}
  ```

  It stops accidents and runaway agents, not the owner, who can disable the
  ruleset. Say so wherever the rule text claims protection.
- **Forge CI on push to the default branch only** (no pull-request trigger): an
  ex post record of when the base went red, from a second, clean environment.
  A red base means the local gate let something through; the response is a fix
  pull request, not a ticket. The author later disabled GitHub Actions altogether, so
  no forge CI runs; GitHub is a sync host.

## The gate record

- A git note on the candidate merge commit, in the notes ref `refs/notes/gate`.
  The latest entry for a commit decides.
- Fields: result, time, actor (runtime, model and effort where known, never
  required), host, revision, command and scope, tool versions, the fast-path
  state when the base declares one (`fastpath:`), one line per check.
- Monitor verdicts on main tips live beside the records, in the notes ref
  `refs/notes/gate-verdict` (ticket 1226); they open and close the fast path.
- The check set is declared in a file on the base branch (`.merge-gate.json`),
  read from the base, so a branch cannot choose its own checks. The checks run
  code from the branch; the file fixes which checks and which commands.
- Fail closed: an unreadable declaration, a malformed file, an empty forge check
  list or a failed inspection refuses the merge; only an explicit `"gate": "off"`
  turns the gate off.
- In place (ticket 1156, closed): the record and the refusal in the merge helper,
  and the activation that turned the gate on.

## The guard on the base branch

- A `reference-transaction` hook journals every update of the base branch (time,
  OS user, host, command lines of the process chain, and git identity). It never
  blocks and never fails loudly.
- It can refuse an update that carries no gate record. That is off by default;
  `git config idh.mainGuard enforce` turns it on, per clone. Install it through
  `core.hooksPath`; a client that overrides it defeats the hook, which is why the
  audit exists. The hook runs `scripts/merge-gate.py` from beside the hooks
  directory; without it no merge passes as gated.
- A daily audit (`scripts/main_sweep.py`) reports every commit that entered the
  base in the last 24 hours without a gate receipt, and exits 2 when it could
  not look in full, never 0. It is git-only: for a forge merge it rebuilds the
  candidate from the merge's two parents and reads the receipt there. It runs
  from the end-of-day wrap-up and by hand, never in the merge path. The hook
  and the audit are built (tickets 1157 and 1179); turning `enforce` on follows
  an observation period (ticket 1180).

## Trust, verify, monitor

The stance behind the gate, written for projects that adopt it.

- **Trust.** The orchestrator that runs a review chooses which perspectives to run, how
  deep, and with which tools: its runtime's own verify and simplify tools, the harness's
  review skill, or none. It is told that external reviewer tools exist for a read from
  another model family when it wants one. The harness fixes no floor and no category of
  change. Mechanical work lives in scripts, not prose, so that a smaller model can follow
  the skills.
- **Verify, always.** A reviewer never approves: only the gate rules. A review result applies
  to one head. The full integration check runs once, on the merge candidate, and writes the
  gate record; a bookkeeping merge on an open fast path runs it on the new main tip
  after the merge instead.
- **Monitor.** The guard journal, the daily audit of commits that entered the base branch, the
  monitor's verdicts on main tips (`refs/notes/gate-verdict`), the
  review result comment (what ran, by which family, why) and the count of review runs per
  pull request show afterwards whether the trust was well placed.

## Review disciplines that go with it

- Stop a review loop when a round finds no defect that is both absent on the base
  branch and over the severity floor; run the cross-family read once, on the final
  head.
- A review perspective that launched and returned no report is re-run once
  before the panel is called degraded. A degraded panel escalates.
- Before delegating a change to a rule that skills state in several places, grep
  every statement of it and hand the delegate the list.
- Thin the test suite on a schedule: tests that only pin wording are the first to
  cut. The testing doctor skill (`/test-doctor`) holds the remedy. **Pending.**

## Direction

The forge stays the central origin: one place to pull from, and the host for
backup, coordination and publication. The host is GitHub, kept on purpose: most
web development tools integrate with it, and the author does not want to give
that up. There is no plan to move merging off it. A peer-to-peer git model or a
self-hosted forge on the author's own machine is not ruled out; it is not
planned either, and nothing here should depend on the host being GitHub.
Some of what lives on the forge today is temporary and is expected to move into
git, pinned to a revision, as the dyne format arrives (git-erg tickets 0270,
0272, 0273): the verdicts and review results now posted as pull-request comments,
and the review threads. The gate record is already a git note for that reason.

## Adopting this in another project

1. Create the light ruleset above; disable any required-checks ruleset only when
   the local gate is running and has been rehearsed once.
2. Copy the gate script, the declaration file, and the merge helper; list the
   project's checks and its light paths (documentation, tickets, memory).
3. Set `core.hooksPath` to the hooks directory and install the journal hook;
   leave the guard in warn mode until the journal has been read for a week.
4. Trim the forge workflow to push on the default branch.
5. Decide who turns `enforce` on; it is the author's act, not an agent's.
6. Run the daily audit from the end-of-day wrap-up, or by hand, and read its
   first report.

## What this does not do

It does not stop a determined owner: the forge settings can be changed and a
client can override the hooks. It makes that visible afterwards. It does not
authenticate a record: anyone can write a note. It does not replace review: the
review gate rules on exit criteria and comments, and the record only says the
checks ran on this exact commit.
