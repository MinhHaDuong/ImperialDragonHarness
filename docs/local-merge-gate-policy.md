# Local merge gate: policy and adoption guide

Status as of 2026-10-21. Written at the author's request so the policy can be
adopted in other projects. Decided in tracker 1045; the parts still being built
are marked **pending** with their ticket.

## Principle

The merge gate is local; the forge is a host, not an authority. Trust is a base
principle, so the gate leaves no open door: it adds traceability. Two things must
be answerable after the fact: what was run (when, by whom, on which host and
revision), and whether anyone got around the gate. A record is a statement that
can be traced, not proof. Nothing depends on one agent runtime: the basis is git
and the forge, which hold for any agent and for a human.

## The flow

The expensive check runs once, last, on the merge candidate. Earlier stages run
only what they need.

| Stage | Where | What runs |
|---|---|---|
| 1. Work | the author's or agent's machine | scoped tests of the touched files |
| 2. Rebase onto the base branch, resolve conflicts | local git | nothing |
| 3. Review (code review and the merge-gate review) | local seats | read the diff; targeted tests of the touched files only |
| 4. Changes needed? | | back to stage 1; no full run yet |
| 5. Candidate | the harness | merge the pull request into the base locally, run the full check set once on that commit, write the gate record |
| 6. Merge | the merge helper | refuses without a passing record on that candidate |

A failed candidate sends the pull request back to stage 1; it then passes through
stages 2, 3 and 5 again. That is the only case where the full set runs twice.
A pure documentation, ticket or memory diff gets a light record (the ticket
validator only), so the trace stays uniform and the cost stays small. **Pending**
(ticket 1171 and the activation pull request of ticket 1156; ticket 1172, reading the forge's result for a head, is paused because this flow makes it unnecessary).

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
  pull request, not a ticket. **Pending** (ticket 1174).

## The gate record

- A git note on the candidate merge commit, in the notes ref `refs/notes/gate`.
  The latest entry for a commit decides.
- Fields: result, time, actor (runtime, model and effort where known, never
  required), host, revision, command and scope, tool versions, one line per check.
- The check set is declared in a file on the base branch (`.merge-gate.json`),
  read from the base, so a branch cannot choose its own checks. The checks run
  code from the branch; the file fixes which checks and which commands.
- Fail closed: an unreadable declaration, a malformed file, an empty forge check
  list or a failed inspection refuses the merge; only an explicit `"gate": "off"`
  turns the gate off.
- **Pending** (ticket 1156): the record and the refusal in the merge helper,
  then the activation pull request that turns the gate on.

## The guard on the base branch

- A `reference-transaction` hook journals every update of the base branch (time,
  OS user, host, command lines of the process chain, git identity). It never
  blocks and never fails loudly.
- It can refuse an update that carries no gate record. That is off by default;
  `git config idh.mainGuard enforce` turns it on, per clone. Install it through
  `core.hooksPath`; a client that overrides it defeats the hook, which is why the
  sweep exists.
- A periodic sweep reports every commit that entered the base without a gate
  record or green forge checks. It uses only git and the forge API and exits 2
  when it could not look, never 0.
- **Pending** (ticket 1157).

## Review disciplines that go with it

- Stop a review loop when a round finds no defect that is both absent on the base
  branch and over the severity floor; run the cross-family read once, on the final
  head.
- A review perspective that launched and returned no report is re-run once
  before the panel is called degraded. A degraded panel escalates.
- Before delegating a change to a rule that skills state in several places, grep
  every statement of it and hand the delegate the list.
- Thin the test suite on a schedule: tests that only pin wording are the first to
  cut. The testing doctor skill (`/pulse`) holds the remedy. **Pending.**

## Adopting this in another project

1. Create the light ruleset above; disable any required-checks ruleset only when
   the local gate is running and has been rehearsed once.
2. Copy the gate script, the declaration file and the merge helper; list the
   project's checks and its light paths (documentation, tickets, memory).
3. Set `core.hooksPath` to the hooks directory and install the journal hook;
   leave the guard in warn mode until the journal has been read for a week.
4. Trim the forge workflow to push on the default branch.
5. Decide who turns `enforce` on; it is the author's act, not an agent's.
6. Put the sweep on a schedule and read its first report.

## What this does not do

It does not stop a determined owner: the forge settings can be changed and a
client can override the hooks. It makes that visible afterwards. It does not
authenticate a record: anyone can write a note. It does not replace review: the
review gate rules on exit criteria and comments, and the record only says the
checks ran on this exact commit.
