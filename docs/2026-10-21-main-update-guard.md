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
  `git fetch --atomic origin main:main`);
- by fast-forward to the main tip this worktree just fetched from `origin`
  (`FETCH_HEAD`), because a plain `git fetch origin main:main` moves main in
  its own transaction before it updates `origin/main`;
- onto a merge commit whose first parent is the current main and which carries
  a gate record, a note in `refs/notes/gate` (ticket 1156). Only the note's
  presence is read here, by `gate_record_present`; the note's format belongs
  to ticket 1156.

Any other update is not gated, including a local commit on main, a reset, a
deletion or a rewind.

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

Until ticket 1156 lands, `enforce` means local main moves only to what the
forge already merged. That is the current practice: PRs merge on the forge and
sync-local-main.sh fast-forwards. Before switching, check `warn`-mode lines in
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

Setting `git -c core.hooksPath=/dev/null …`, editing the hook, or writing
`FETCH_HEAD` by hand defeats the hook. Following the merge-gate spec §4.4, the
guard stops accidents. It does not stop intent. The sweep covers the rest.

## The sweep: `scripts/main_sweep.py`

For each first-parent commit of `origin/main` it reports two facts: whether a
gate record is present, and the PR whose merge commit it is, with that PR's
required check conclusions on its head. The required check names come from the
rulesets on main, read even when disabled; `main-required-checks` was disabled
on 2026-10-21. A commit is `ok` when it has a record or green checks, a
`finding` when it has neither, and `unknown` when the forge could not be read
and no record decides. Exit codes: 0 all ok, 1 a finding, 2 could not look
(an empty range counts as could not look).

```sh
make main-sweep                                   # last 8 days, fetches main and the notes
python3 scripts/main_sweep.py --max-count 200 --json
```

Periodic run, runtime-free, for example from the author's crontab on the
authority host:

```cron
17 6 * * * cd ~/.agents && make -s main-sweep >/dev/null || echo "main sweep: exit $?" | mail -s "main sweep" "$USER"
```

Choosing the schedule and where a finding goes (a mail, a ticket, a molt step)
is left to the author.
