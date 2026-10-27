# Local merge gate: policy and adoption guide

Status as of 2026-10-21. Written at the author's request so the policy can be
adopted in other projects. Decided in tracker 1045. Today only the forge
settings are in place (the light ruleset, no required checks, GitHub Actions
disabled), together with the gate-record machinery, the guard hook and the daily audit.
The gate itself switches on when the activation pull request of ticket 1156
merges. Each part still open is marked **pending** with its ticket.

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
(ticket 1171 and the activation pull request of ticket 1156). Ticket 1172, reading the forge's result for a head, was closed as superseded by this flow.

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

## Session credential

One place states which credential agent sessions use (ticket 1196).

- **Sessions run as a narrow identity.** `scripts/bash-env.sh` exports
  `GH_CONFIG_DIR=$HOME/.config/gh-agent` into agent shells when
  `$HOME/.config/gh-agent/hosts.yml` exists. That gh config dir is logged in with a
  fine-grained personal access token: contents and pull requests read/write; issues,
  metadata and commit statuses read; no administration, workflows or Actions. The
  variable is a path, not a secret; the token lives only in that config and in
  `~/.config/keys/github.env`.
- **The owner login is the author's.** The default gh login (the repository owner) stays
  for the author's admin acts: rulesets, settings, Actions. The author's interactive shell
  does not load `bash-env.sh`, so it keeps that login.
- **Measured.** With the agent credential a ruleset POST and a repository settings PATCH
  answer 403. Pull requests 1792, 1793, 1794, 1796 and 1797 merged end to end with
  `raid_land.py` on it. The repository has no CI, so check-run reads are untested.
- **Git pushes over ssh use the author's key.** They are not gh calls: they can push
  branches and `refs/notes/*`, and cannot reach any admin API.
- **Loader coverage.** `BASH_ENV` is wired into Claude Code settings only
  (`adapters/lifecycle.py`; the projection of `bash-env.sh` lists the claude runtime).
  Codex and Pi shells do not load it, so there the agent credential is not selected
  automatically: the gap stays open until those adapters wire an equivalent.
- **Limitation, measured.** The `main-traceability` ruleset covers only `main`.
  `refs/notes/*`, including `refs/notes/gate` (the gate record), stay writable and
  deletable by the session credential
  (ticket 1277's notes-transport trial, measured on a throwaway notes ref; its report is
  `conception/2026-10-27-notes-transport-trial.md` once that branch lands).
- `scripts/census/permissions.py` audits permission allow rules, not credentials, and
  does not state this.

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
  gate record.
- **Monitor.** The guard journal, the daily audit of commits that entered the base branch, the
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
