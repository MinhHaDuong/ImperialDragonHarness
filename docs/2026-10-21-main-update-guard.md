# Main-update guard

Ticket 1157, child B of tracker 1045. Two parts. The first is a git hook that
journals every update of `refs/heads/main` and can refuse one. The second is a
periodic sweep that reports any commit that reached `main` without a gated
merge. Both use only git and the forge's API, so they work the same under any
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
- onto a merge commit (two parents or more) whose first parent is the current
  main and which carries a gate record, a note in `refs/notes/gate` (ticket
  1156). Only the note's presence is read here, by `gate_record_present`; the
  note's format belongs to ticket 1156.

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

### Bypass boundary

Each of these defeats the hook with enforce on:
- `git -c core.hooksPath=/dev/null …`, or editing the hook;
- writing `FETCH_HEAD` by hand;
- moving `refs/remotes/origin/main` in one command, then main to it in another;
- adding a note in `refs/notes/gate` by hand on a merge built on main: any
  note counts until ticket 1156's record carries checks the hook can read;
- making the command line look like a fetch while moving `origin/main` and
  main in one transaction, for example `git update-ref -m ' fetch ' --stdin`,
  or `git fetch . +X:refs/remotes/origin/main +X:refs/heads/main`. The hook
  reads the command line, so a deliberate imitation passes; only intent
  reaches it, and more heuristics would not close it.

Following the merge-gate spec
([`docs/2026-10-05-merge-gate-spec.md`](2026-10-05-merge-gate-spec.md),
"Holding the line on `main`"), the guard stops accidents. It does not stop
intent. The sweep covers the rest.

## The sweep: `scripts/main_sweep.py`

For each first-parent commit of `origin/main` it reports two facts: whether a
gate record is present, and the PR whose merge commit it is, with that PR's
required check conclusions on its head. It reads check runs only, not legacy
commit statuses. The required check names come from the rulesets on main, read
even when disabled; `main-required-checks` was disabled by the author on
2026-10-21.

A commit is `ok` when it has a record or green checks, a `finding` when it has
neither, and `unknown` when the forge could not be read and no record decides.
Exit codes: 0 all ok, 1 a finding, 2 could not look. A finding wins: exit 1
even when causes of "could not look" are also present. "Could not look" covers
a failed `--fetch` of main or of the gate records, an unknown ref, missing
`gh` or git, malformed forge output, unreadable required check names, an empty
range, and a range cut by `--max-count` (default 100; `make main-sweep` uses
1000). The report names each cause on an `incomplete:` line, for example
`incomplete: empty range: no commit to sweep`.

```sh
make main-sweep                                   # last 8 days, fetches main and the notes
python3 scripts/main_sweep.py --max-count 200 --json
```

Periodic run, runtime-free, for example from the author's crontab on the
authority host. It runs `make main-sweep`, so its flags stay those of the
Makefile, and the report goes into the mail, so a finding arrives with its
commits named (make exits non-zero for both a finding and "could not look";
the report says which):

```cron
17 6 * * * cd ~/.agents && f=$(mktemp) && { make -s main-sweep > "$f" 2>&1 || mail -s "main sweep: not clean" "$USER" < "$f"; rm -f "$f"; }
```

Choosing the schedule and where a finding goes (a mail, a ticket, a molt step)
is left to the author.
