# Main-update guard

Ticket 1157, child B of tracker 1045. Two parts. The first is a git hook that
journals every update of `refs/heads/main` and can refuse one. The second is a
daily audit that reports any commit that reached `main` in the last 24 hours
without a gate receipt. Both use only git, so they work the same under any
agent runtime and for a human.

## The hook: `hooks/reference-transaction`

git runs it for every ref transaction: commit, fetch, `update-ref`,
`branch -f`, reset, rebase, and the same from a linked worktree. `--no-verify`
does not skip it. It returns at once unless the transaction touches
`refs/heads/main`.

**Journal.** One JSON line per phase (`prepared`, `committed`, `aborted`) in
`$(git rev-parse --git-common-dir)/idh/main-journal.jsonl`, shared by all
worktrees. Each line holds the time (UTC), OS user and uid, host, cwd, the git
committer identity, the declared old, current and new values, and the command
line of each process from git up to the session. At `prepared` it also records
the decision and the action taken. A journal error is swallowed and never
aborts the update.

**Gated update.** main may move:
- to `origin/main`, or by fast-forward along it (sync-local-main.sh, `git pull`,
  `git fetch --atomic origin main:main`). Only a `fetch` may vouch for main
  with an `origin/main` value carried in the same transaction; any other
  command is judged against the `origin/main` already on disk;
- by fast-forward to the main tip this worktree just fetched from `origin`
  (`FETCH_HEAD`), because a plain `git fetch origin main:main` moves main in
  its own transaction before it updates `origin/main`;
- onto a merge commit of exactly two parents whose first parent is the
  current main, whose tree is that of the candidate `scripts/merge-gate.py
  candidate` rebuilds from those parents, and whose candidate carries a
  passing receipt in `refs/notes/gate` (ticket 1156), as `scripts/merge-gate.py
  check --no-fetch` decides (see "Matching a merge to its receipt" below).

Any other update is not gated, including a local commit on main, a reset, a
deletion or a rewind. A `verify` of main inside `git update-ref --stdin` is not
an update and is ignored. A `delete` of main with an expected old value inside
`update-ref --stdin` reaches the hook in the same shape as a `verify`, so it
cannot be refused; once committed it is journaled (`deleted-unrefusable`) and
warned about.

### How this differs from the merge-gate spec

The spec ([`docs/2026-10-05-merge-gate-spec.md`](2026-10-05-merge-gate-spec.md),
"Holding the line on `main`") lets main move only onto a commit with a
`checks pass` note, its first parent equal to the old main, and a second
parent carrying an APPROVED verdict. The built hook differs in three ways:
- it accepts any non-empty note in `refs/notes/gate`, not only a `checks pass`
  one: the record's format and its checks belong to ticket 1156;
- it does not look for a verdict on the second parent: the verdict belongs to
  the review gate (`/verify-gate`, and `/merge`'s refusal in ticket 1156);
- it adds the on-origin path, so that the forge's merges, synced locally,
  stay allowed.

**Mode**, read from `git config idh.mainGuard`:

| Value | Not-gated update |
|---|---|
| `warn` (default; also any unset or unknown value) | journaled, one stderr warning, allowed |
| `enforce` | journaled, refused at `prepared` |
| `off` | journaled only |

### Turning enforce on (the author's act)

```sh
git -C ~/.agents config idh.mainGuard enforce   # shared by every worktree
git -C ~/.agents config --unset idh.mainGuard   # back to warn
```

Without a gate record writer in use, `enforce` means local main moves only to
what the forge already merged. That is the practice today: PRs merge on the
forge and sync-local-main.sh fast-forwards. Before switching, check `warn`-mode lines in
the journal (`"action":"warned"`) for a legitimate flow that would be refused.

### Verifying the installation

This repository sets `core.hooksPath=hooks`, so a hook in `.git/hooks` never
runs. The path is relative: each worktree runs the `hooks/` of its own
checkout. A worktree whose branch predates this hook runs no guard. Check what
git will actually run:

```sh
git rev-parse --git-path hooks/reference-transaction   # must print hooks/reference-transaction
test -x "$(git rev-parse --git-path hooks/reference-transaction)"
```

`tests/test_main_guard_hook.py` checks this resolution in a clone and in a
linked worktree.

The hook runs `scripts/merge-gate.py` from beside its own directory
(`hooks/../scripts/`) to rebuild a merge's candidate and read its receipt;
the script and `python3` must be present there. Without them, no merge
passes as gated: in `enforce` a local merge is refused (fails closed), in
`warn` it is journaled and warned about. A hook copied alone into
`.git/hooks`, with no `scripts/` beside it, therefore treats every gated
merge as not gated; the on-origin path does not need the script.

### Bypass boundary

Each of these defeats the hook with enforce on:
- `git -c core.hooksPath=/dev/null …`, or editing the hook;
- writing `FETCH_HEAD` by hand;
- moving `refs/remotes/origin/main` in one command, then main to it in another;
- writing a passing record in `refs/notes/gate` by hand on the candidate of a
  merge built on main: anyone can write a note, and a record is a statement,
  not proof;
- making the command line look like a fetch while moving `origin/main` and
  main in one transaction, for example `git update-ref -m ' fetch ' --stdin`,
  or `git fetch . +X:refs/remotes/origin/main +X:refs/heads/main`. The hook
  reads the command line, so a deliberate imitation passes; only intent
  reaches it, and more heuristics would not close it.

Following the merge-gate spec
([`docs/2026-10-05-merge-gate-spec.md`](2026-10-05-merge-gate-spec.md),
"Holding the line on `main`"), the guard stops accidents. It does not stop
intent. The audit covers the rest.

## Matching a merge to its receipt

The merge gate writes its receipt on the candidate: the `--no-ff` merge of
the branch head into the base tip, built with fixed author, committer, date
and message, so any host rebuilds the same object id from the same two
parents. The forge's merge commit M has the same parents and tree but other
metadata, so it is another object and carries no note. For a merge M with
exactly two parents (P1, P2), the hook and the audit rebuild the candidate
from (P1, P2) with `candidate()` of `scripts/merge-gate.py`, the one builder,
require M's tree to equal the candidate's, and let the latest entry on the
candidate decide (`decide()`: pass, under the scope P1 declares). Matching by
parents alone would let a merge with the gated parents but edited content, or
an octopus with an extra parent, borrow a receipt. A receipt made before the
base moved names the candidate of the old base tip; the candidate of (P1, P2)
then has no note, and the merge is a finding.

## The audit: `scripts/main_sweep.py`

Stateless and git-only: no forge read, no watermark, no stored state. It
reads the repository it runs in, so any project that adopts the gate can run
it, and prints nothing when the tip of `--ref` (default `origin/main`)
declares no gate (`.merge-gate.json` absent or `"gate": "off"`). With
`--fetch`, main is fetched before that check, so the first run after a
project turns the gate on sees it; the receipts are fetched only when the
gate is on.

**Window.** Git records when a commit was made, not when it entered main;
the committer date is the only clock, and it can be set by hand. The audit
walks the newest `--max-count` first-parent commits of `--ref` (default 200)
and covers every one from the tip down to the deepest one dated in the last
24 hours. A backdated commit above a recent one is covered, and cannot hide
the commits below it. A recent commit below more than `--max-count` older
ones stays out of reach.

Each covered commit gets one line:
- `ok`: a two-parent merge whose tree is its rebuilt candidate's and whose
  candidate carries a passing receipt, or a single-parent commit with a note
  on itself;
- `finding`: no receipt (none, or made on another base tip), a failing or
  out-of-scope receipt, a tree that differs from the candidate's, a merge of
  more than two parents, a candidate that cannot be rebuilt, or a parentless
  commit whose own tree declares the gate (an orphan pushed as main);
- `ungated`: its first parent declared no gate, so the commit predates it.

Exit codes: 0 no finding, 1 a finding, 2 could not look in full. Hitting the
commit cap or the time limit (`--time-limit`, default 60 s) prints `range cut
at …` and exits 2, whatever it found. A failed `--fetch`, an unreadable
declaration or an unknown `--ref` also exits 2.

```sh
make main-sweep                          # fetches main and the receipts, then audits
python3 scripts/main_sweep.py --summary  # one line, as the end-of-day wrap-up carries it
```

It never runs in the merge path: not among the gate's checks, not in the
merge helper. The end-of-day wrap-up (`/lair`) runs it with `--summary` and
carries its line, `main audit: N commits in the last 24 h, M without a gate
receipt: <first>`, where N counts every covered commit, merges and others;
otherwise it runs by hand.
