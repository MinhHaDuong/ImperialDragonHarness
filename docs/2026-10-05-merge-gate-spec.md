# Merge gate — draft spec

Status: draft 1, 2026-10-05, not adopted. Draft 0 reviewed by sol (`gpt-6.1-sol`,
medium, read-only, via codex); draft 1 not re-reviewed. Applicability checked
against the eight projects of `scripts/projects.json`. Author: Claude, for the
maintainer. Tracked by ticket 1045.
Home: harness `docs/` while a draft; normative text moves to git-erg (`dyne`,
tickets 0272/0273) once settled.

Decided since this draft was written (2026-10-06), and not reflected below:
- The local runner it assumed now exists (`scripts/local-ci.sh`, ticket 1041,
  PR 1218). It reproduces the forge CI; it does not gate merges.
- A bypass of the forge's ruleset for outages was tried and reverted by the
  author: waiting is preferred to bypassing. §7's "fallback: run the checks by
  hand and write the note" is therefore not wanted as a way around the forge.
- A `pre-push` hook (an "advisory" local run) was dropped as not worth its cost.
- Trust is a base principle of IDH: no open door. §3's "no contributors, so a
  self-declaration is accepted" is not the reasoning to keep; the requirement is
  traceability of what was run, when, by whom, on which host and revision.
- The ruleset `main-required-checks` requires seven forge checks; three CI jobs
  run but are not required. The content of the CI is to be reviewed before this
  gate is built.

## 1. Purpose

Replace the forge's "CI must be green" rule with a **merge gate** held by git
itself: the conditions under which `main` may move, checked on the
maintainer's own machines, recorded in the repository, enforced without a
server.

Trigger: GitHub Actions stopped provisioning runners (2026-10-05) and every PR
blocked. The gate must not depend on a forge being up.

## 2. Vocabulary

"CI" is dropped: it names a forge service, and what we want is a gate.

| Term | Meaning |
|---|---|
| **checks** | Mechanical, reproducible commands run on a commit. Pass or fail. |
| **verdict** | A judgement on a branch head: `APPROVED`, `REROLL`, `ESCALATE` (today `/gaze` + `/verify-gate`). |
| **merge gate** | The conjunction required before `main` moves: checks pass on the **candidate** and verdict APPROVED on the **branch head**. |
| **candidate** | The exact commit that will become `main`: the `--no-ff` merge of the branch into current `main`, hook effects included. |
| **authority** | The one machine on which `main` moves. |

The gate is a **hook-enforced local policy**, not an immutable property of
version control (§4.4).

## 3. Non-goals

- No server, no bare remote, no daemon, no webhook.
- No contributors: the threat is an accident (an agent session updating
  `main`, a forgotten step), not an adversary. No sandbox for the checks.
- No replacement of review: verdicts keep their meaning, only their pinning moves.
- Not a CI product: no matrix, no cache, no artifacts.

## 4. Mechanism

### 4.1 Build the candidate, then check it

Draft 0 pinned a tree hash and merged afterwards. Review finding: merge-time
hook effects (`erg close` edits `tickets/`) would then reach `main` untested.
The gate therefore checks what will actually land.

`gate merge <branch>`, on the authority:

1. Refuse unless the branch has a verdict APPROVED pinned to its current head
   commit (full OID), with no later REROLL or ESCALATE for that head (§4.3).
2. In a throwaway worktree, build the candidate: `--no-ff` merge of the branch
   head into the current `main`, then run the merge hooks and stage their
   changes into the merge commit (0270 "atomic merge").
3. Run the project's checks command in that worktree.
4. On pass, write the evidence (§4.2), then move `main` to the candidate with a
   conditional update: `update-ref refs/heads/main <candidate> <expected-old>`.
   If `main` advanced meanwhile, the update fails and the gate restarts at 2.

Rebasing the branch is not required: the candidate is built against current
`main` every time, so "a gate validates branch ⊕ base" holds by construction.

### 4.2 Evidence

Checks evidence is a note on the candidate commit, in `refs/notes/gate`:

    checks pass host=padme cmd="make check-tests" scope=full versions="bash 5.2 grep 3.11 …"

`scope` is `full`, or `selected:<…> skipped:<…>` for a scoped gate
(`.idh-checks.json`); a scoped pass is never recorded as `full`.

Why a note and not a log line in `merges/<branch>.dyne` (0270): the candidate
does not exist until the merge is built, and writing into the file would change
the commit just checked (the draft 0 pin problem). Verdicts, which concern a
branch head that exists in advance, stay as log lines in the `.dyne` file as
0270 specifies. After the merge, the checks line is copied into the archived
`.dyne` file by a follow-up commit if the maintainer wants it in the tree
(open question 1).

### 4.3 Supersession

For one subject (a branch head for a verdict; a candidate for checks), the
**latest entry decides**. `APPROVED` then `REROLL` on the same head: rejected.
`checks fail` after `checks pass` on the same candidate: rejected; a re-run is
a new entry, and the newest wins. Ties (same timestamp) reject.

### 4.4 Holding the line on `main`

A `reference-transaction` hook refuses any update of `refs/heads/main` whose
new commit lacks, at the `prepared` phase, all of: a `checks pass` note, its
first parent equal to the old value, and a second parent carrying an APPROVED
verdict. The hook reads the proposed old and new OIDs, so it needs no
environment flag and cannot be authorised by a flag a child process inherited.
It fires for fast-forward, rebase, `update-ref` and linked worktrees alike;
`--no-verify` does not bypass it.

Installation is verified, not assumed. `gate install` resolves the effective
hook path with `git rev-parse --git-path hooks/reference-transaction` (this
repository sets `core.hooksPath=hooks`, which a hook placed in `.git/hooks`
would never reach) and fails if the resolved file is not the installed one.

Bypass boundary, stated plainly: `git -c core.hooksPath=/dev/null …` or
editing the hook defeats it. Under §3 that is accepted; the gate stops
accidents, not intent.

### 4.5 Two machines, one authority

`padme` and `doudou` exchange branches by `git fetch` over SSH. `main` moves on
one machine only, the authority (default `padme`); the other fetches `main`
into a tracking ref and never merges locally. If the authority is down, no
merge: the fallback is to run the checks by hand and write the note, a
self-declaration, accepted under §3. Either machine may run `gate checks` on a
branch to pre-validate it (advisory, not the gate).

## 5. Per-project declaration

A project opts in. Two independent switches:

    gate   = on | off      # off: no hook installed, main moves as today
    checks = <command> | none   # none: the gate reduces to the verdict

`checks = none` does not mean `gate = off`; the verdict and hook restrictions
still apply. Neither is a default: an unconfigured project is `gate = off`.

## 6. Migration

1. **One definition of checks.** The GitHub workflow's inline shell becomes
   tests (marker `adherence`, auto-tests included), so that `make check-tests`
   plus `erg check tickets/` is everything CI ran. Pure refactor; validate by
   making each guard fail on purpose before and after.
2. `gate merge` (§4.1–4.3) and notes.
3. `reference-transaction` hook and `gate install` (§4.4).
4. Remove the project's GitHub workflow once 1–3 hold there.

Steps 2–3 belong to dyne (0272/0273: format and `dyne merge`). Step 1 stands
alone and is useful at once.

## 7. Known weaknesses

- A pass written on the author's own machine is a self-declaration (§3).
- The checks environment is the host's, not a clean image: a pass on one host
  can fail on the other (grep, awk, age). Mitigation: record versions; run on
  both hosts for changes touching shell or the toolchain.
- `cross-pr-ticket-collision` reads open PRs from the GitHub API. Under dyne,
  "open" is a remote branch that is not an ancestor of `main` (0270), fresh as
  of the last fetch. Needs rewriting.
- The gate holds only where the hook is installed and `core.hooksPath` is not
  overridden (§4.4).

## 8. Open questions

1. Evidence home: notes on the candidate (this draft) versus 0270's log line in
   the `.dyne` file (needs a pin that survives appending). Sol's alternative:
   pin a full candidate commit and allow an evidence-only successor commit.
   The notes route departs from "the register is the tree".
2. Sign entries (GPG, already used for releases)? Not needed under §3.
3. Whether the authority may be Doudou when Padmé is down (a one-line
   `authority =` change, but both `main`s must then be reconciled by hand).

## 9. Applicability to the eight projects

Facts from a read-only survey by a cheap agent (Haiku), unverified in detail:
it misreported the harness CI as 3 jobs when `CI.yml` has 10, and its summary
miscounts in two places. Treat the table as a map, not as evidence.

| Project | Kind | Has CI today | Verdict for the gate |
|---|---|---|---|
| harness | Python, shell | yes, 10 jobs | **Applicable now.** The origin of the need. |
| git-erg | Go | yes (+ `rebuild-binary.yml`) | **Applicable.** The committed binary is rebuilt by a workflow: the gate must rebuild it deterministically, or step 4 cannot remove that workflow. |
| AEDIST-technical-report | Python + LaTeX | yes (+ docs build) | **Partly.** Code branches yes; the report prose is edited in place on `main`. |
| chemin-de-voix | Python, GPU, LLM | none | **No gain.** No gate today; the full check needs CUDA and API keys, so only `check-fast` could be gated. |
| climate-finance-het | Python, large data | none | **No gain.** Full check depends on data under `~/data` (host-bound); gate `check-fast` at most. |
| fuzzy-corpus | Python + LaTeX | none | **No.** Prose is edited in place. |
| cadens | Python + LaTeX | none | **No.** Same. |
| padme | Markdown logbook | none | **No.** Nothing to check; edited in place. |

Findings:

1. **Prose repos collide with the hook.** `git.md` lets the author commit
   manuscript prose to `main` directly. A `reference-transaction` hook on
   `main` would block it. The gate must be opt-in per repository (§5), and a
   mixed code-and-paper repo needs either `gate = off` or a path scope, which
   this draft does not specify. Until it does, mixed repos stay `off`.
2. **Real scope is two or three repos.** Only harness, git-erg and AEDIST have
   a forge gate to replace. For the five others the gate adds work and removes
   nothing; they would merely gain a check they never had.
3. **Heavy checks are host-bound.** Where checks need a GPU or the corpus under
   `~/data`, `host=` stops being informational: the gate is only satisfiable on
   one machine. Declare the fast subset as `checks`.
4. **Universal common denominator.** All eight use `tickets/*.erg`, so
   `erg check tickets/` is the one check every opted-in project can run.
5. **No project has `.idh-checks.json`.** The scoped-gate path (`scope=selected`)
   is unexercised outside the harness; do not rely on it in v1.
6. **dyne does not exist yet.** Steps 2–3 wait on 0272/0273. Meanwhile the
   harness can run step 1 and a hand-written `make gate` (build candidate,
   check, move `main`), without the hook.
